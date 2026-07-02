import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def initialize(self) -> None:
        logger.info("Loading embedding model '%s'...", self._model_name)
        self._model = SentenceTransformer(self._model_name)
        logger.info(
            "Embedding model loaded. dimension=%d", self.get_dimension()
        )

    def embed(self, text: str) -> list[float]:
        if self._model is None:
            raise RuntimeError("EmbeddingModel not initialized")
        vector: np.ndarray = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            raise RuntimeError("EmbeddingModel not initialized")
        vectors: np.ndarray = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def get_dimension(self) -> int:
        if self._model is None:
            return 384
        return self._model.get_embedding_dimension()
