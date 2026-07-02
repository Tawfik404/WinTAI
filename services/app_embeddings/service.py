import logging
import re

import numpy as np

from services.app_embeddings.model import EmbeddingModel
from services.app_embeddings.index import AppIndex, AppVector
from services.app_embeddings.search import find_top_k

logger = logging.getLogger(__name__)


def generate_aliases(name: str) -> list[str]:
    """Generate semantic aliases for an app name to improve embedding search recall."""
    original = name.strip()
    if not original:
        return []

    lower = original.lower()
    seen: set[str] = set()
    aliases: list[str] = []

    def _add(a: str) -> None:
        a = a.strip()
        if a and a.lower() not in seen and a.lower() != lower:
            seen.add(a.lower())
            aliases.append(a)

    _BRAND_PREFIXES = [
        "microsoft ", "google ", "mozilla ", "apple ",
        "adobe ", "oracle ", "intel ", "nvidia ", "amd ",
    ]
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

    cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', original).strip()
    if cleaned and cleaned != original:
        _add(cleaned)

    return aliases


class AppEmbeddingService:
    def __init__(self) -> None:
        self._model = EmbeddingModel()
        self._index = AppIndex()
        self._initialized = False

    def initialize(self, apps: list[dict]) -> None:
        if not apps:
            logger.warning("No apps provided — index is empty")
            self._initialized = True
            return

        self._model.initialize()
        names = [a["name"] for a in apps]

        # Batch 1: primary name embeddings
        vectors = self._model.embed_batch(names)

        # Collect all alias texts with their app index for batch embedding
        alias_texts: list[tuple[str, int]] = []
        for i, app in enumerate(apps):
            for alias in generate_aliases(app["name"]):
                alias_texts.append((alias, i))

        # Batch 2: all alias embeddings in a single call
        if alias_texts:
            alias_vectors = self._model.embed_batch([t[0] for t in alias_texts])
        else:
            alias_vectors = []

        # Distribute alias embeddings back to their apps
        app_alias_embeddings: list[list[np.ndarray]] = [[] for _ in apps]
        for (_, app_idx), vec in zip(alias_texts, alias_vectors):
            app_alias_embeddings[app_idx].append(
                np.array(vec, dtype=np.float32)
            )

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

        total_vectors = self._index.size + sum(
            len(v.alias_embeddings) for v in app_vectors
        )
        logger.info(
            "App embedding index ready: %d apps, %d total vectors (dimension=%d)",
            self._index.size,
            total_vectors,
            self._model.get_dimension(),
        )

    def search(self, query: str, top_k: int = 5) -> dict:
        if not self._initialized or self._index.size == 0:
            return {"name": "", "path": "", "source": "", "confidence": 0.0, "fallback_used": False}

        query_vec = self._model.embed(query)
        ranked = find_top_k(query_vec, self._index, top_k=top_k)

        if not ranked:
            return {"name": "", "path": "", "source": "", "confidence": 0.0, "fallback_used": False}

        logger.info(
            "App search '%s': candidates=%s",
            query,
            [(e.name, round(s, 4)) for e, s in ranked],
        )

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
