import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np

from services.app_embeddings.model import EmbeddingModel
from services.app_embeddings.index import AppIndex, AppVector
from services.app_embeddings.search import find_top_k

logger = logging.getLogger(__name__)

_BRAND_PREFIXES = [
    "microsoft ", "google ", "mozilla ", "apple ",
    "adobe ", "oracle ", "intel ", "nvidia ", "amd ",
]
_TRAILING_PARENS_RE = re.compile(r"\s*\([^)]*\)\s*$")


def generate_aliases(name: str) -> list[str]:
    """Generate semantic aliases for an app name to improve embedding search recall."""
    original = name.strip()
    if not original:
        return []

    lower = original.lower()
    seen: set[str] = set()
    aliases: list[str] = []

    def _add(alias: str) -> None:
        alias = alias.strip()
        if alias and alias.lower() not in seen and alias.lower() != lower:
            seen.add(alias.lower())
            aliases.append(alias)

    for prefix in _BRAND_PREFIXES:
        if lower.startswith(prefix):
            rest = original[len(prefix):].strip()
            if rest and len(rest) > 1:
                _add(rest)
                break

    if "visual studio code" in lower:
        _add("VS Code")
        _add("VSCode")
        _add("Code")
    if "visual studio" in lower and "code" not in lower:
        _add("VS")
    if "postman" in lower:
        _add("Postman")
    if "powershell" in lower:
        _add("PowerShell")
        _add("pwsh")

    cleaned = _TRAILING_PARENS_RE.sub("", original).strip()
    if cleaned and cleaned != original:
        _add(cleaned)

    return aliases


class AppEmbeddingService:
    def __init__(self) -> None:
        self._model = EmbeddingModel()
        self._index = AppIndex()
        self._initialized = False

    @property
    def model_name(self) -> str:
        return self._model.model_name

    def initialize(self, apps: list[dict]) -> None:
        if not apps:
            self._initialized = True
            return

        self._model.initialize()
        names = [a["name"] for a in apps]
        vectors = self._model.embed_batch(names)

        alias_texts: list[tuple[str, int]] = []
        for i, app in enumerate(apps):
            for alias in generate_aliases(app["name"]):
                alias_texts.append((alias, i))

        if alias_texts:
            alias_vectors = self._model.embed_batch([t[0] for t in alias_texts])
        else:
            alias_vectors = []

        app_alias_embeddings: list[list[np.ndarray]] = [[] for _ in apps]
        for (_, app_idx), vec in zip(alias_texts, alias_vectors):
            app_alias_embeddings[app_idx].append(np.array(vec, dtype=np.float32))

        app_vectors: list[AppVector] = []
        for i, (app, vec) in enumerate(zip(apps, vectors)):
            try:
                app_vectors.append(
                    AppVector(
                        name=app["name"],
                        path=app.get("path", ""),
                        source=app.get("source", ""),
                        embedding=np.array(vec, dtype=np.float32),
                        alias_embeddings=app_alias_embeddings[i],
                    )
                )
            except Exception:
                logger.warning("Skipping bad app entry: %s", app.get("name", "?"))
                continue

        self._index.build(app_vectors)
        self._initialized = True

    def initialize_or_load(self, apps: list[dict], cache_path: Path) -> bool:
        fingerprint = self.fingerprint(apps)
        if self.load_index(cache_path, fingerprint):
            return True
        self.initialize(apps)
        self.save_index(cache_path, fingerprint)
        return False

    def load_index(self, cache_path: Path, fingerprint: str) -> bool:
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if payload.get("fingerprint") != fingerprint:
                return False
            if payload.get("model") != self.model_name:
                return False
            entries = []
            for item in payload.get("entries", []):
                entries.append(
                    AppVector(
                        name=str(item["name"]),
                        path=str(item.get("path", "")),
                        source=str(item.get("source", "")),
                        embedding=np.array(item["embedding"], dtype=np.float32),
                        alias_embeddings=[
                            np.array(vec, dtype=np.float32)
                            for vec in item.get("alias_embeddings", [])
                        ],
                    )
                )
            self._index.build(entries)
            self._initialized = True
            return True
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return False

    def save_index(self, cache_path: Path, fingerprint: str) -> None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, Any] = {
                "version": 1,
                "model": self.model_name,
                "fingerprint": fingerprint,
                "entries": [
                    {
                        "name": entry.name,
                        "path": entry.path,
                        "source": entry.source,
                        "embedding": entry.embedding.tolist(),
                        "alias_embeddings": [v.tolist() for v in entry.alias_embeddings],
                    }
                    for entry in self._index.entries
                ],
            }
            cache_path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            logger.warning("Failed to write app embedding cache", exc_info=True)

    def search(self, query: str, top_k: int = 5) -> dict:
        if not self._initialized or self._index.size == 0:
            return {"name": "", "path": "", "source": "", "confidence": 0.0, "fallback_used": False}

        query_vec = self._model.embed(query)
        ranked = find_top_k(query_vec, self._index, top_k=top_k)

        if not ranked:
            return {"name": "", "path": "", "source": "", "confidence": 0.0, "fallback_used": False}

        best_entry, best_score = ranked[0]
        return {
            "name": best_entry.name,
            "path": best_entry.path,
            "source": best_entry.source,
            "confidence": round(best_score, 4),
            "fallback_used": False,
        }

    def get_index_size(self) -> int:
        return self._index.size

    def fingerprint(self, apps: list[dict]) -> str:
        normalized = sorted(
            (
                {
                    "name": str(app.get("name", "")),
                    "path": str(app.get("path", "")),
                    "source": str(app.get("source", "")),
                }
                for app in apps
            ),
            key=lambda app: (app["name"].lower(), app["path"].lower(), app["source"].lower()),
        )
        payload = {"model": self.model_name, "apps": normalized}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

