import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from services.embeddings.index import VectorIndex
from services.embeddings.model_cache import get_sentence_transformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Any | None = None
        self._index = VectorIndex()

    @property
    def model_name(self) -> str:
        return self._model_name

    def initialize(self) -> None:
        if self._model is not None:
            return
        self._model = get_sentence_transformer(self._model_name)

    def embed(self, text: str) -> list[float]:
        if self._model is None:
            self.initialize()
        vector: np.ndarray = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            self.initialize()
        vectors: np.ndarray = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def search(
        self, query_text: str, top_k: int = 5
    ) -> list[tuple[str, float]]:
        query_vec = self.embed(query_text)
        return self._index.search(query_vec, top_k=top_k)

    def get_dimension(self) -> int:
        if self._model is None:
            return 384
        return self._model.get_embedding_dimension()

    def build_index(
        self, tool_descriptions: list[tuple[str, str]]
    ) -> None:
        if not tool_descriptions:
            self._index.clear()
            return
        ids, descriptions = zip(*tool_descriptions)
        vectors = self.embed_batch(list(descriptions))
        self._index.build(list(zip(ids, vectors)))

    def build_or_load_index(
        self,
        tool_descriptions: list[tuple[str, str]],
        cache_path: Path,
    ) -> bool:
        fingerprint = self.fingerprint(tool_descriptions)
        if self.load_index(cache_path, fingerprint):
            return True
        self.build_index(tool_descriptions)
        self.save_index(cache_path, fingerprint)
        return False

    def load_index(self, cache_path: Path, fingerprint: str) -> bool:
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if payload.get("fingerprint") != fingerprint:
                return False
            if payload.get("model") != self._model_name:
                return False
            records = payload.get("records", [])
            self._index.load_records([(str(r[0]), r[1]) for r in records])
            return True
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False

    def save_index(self, cache_path: Path, fingerprint: str) -> None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, Any] = {
                "version": 1,
                "model": self._model_name,
                "fingerprint": fingerprint,
                "records": self._index.to_records(),
            }
            cache_path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            logger.warning("Failed to write tool embedding cache", exc_info=True)

    def fingerprint(self, tool_descriptions: list[tuple[str, str]]) -> str:
        payload = {
            "model": self._model_name,
            "tools": sorted(tool_descriptions),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @property
    def index(self) -> VectorIndex:
        return self._index
