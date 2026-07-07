import logging
from typing import Any

import numpy as np

from services.embeddings.model_cache import get_sentence_transformer

logger = logging.getLogger(__name__)


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Any | None = None

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

    def get_dimension(self) -> int:
        if self._model is None:
            return 384
        return self._model.get_embedding_dimension()
