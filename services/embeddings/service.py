import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from services.embeddings.index import VectorIndex

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._index = VectorIndex()

    def initialize(self) -> None:
        logger.info("Loading embedding model '%s'...", self._model_name)
        self._model = SentenceTransformer(self._model_name)
        logger.info(
            "Embedding model loaded. Dimension=%d", self.get_dimension()
        )

    def embed(self, text: str) -> list[float]:
        if self._model is None:
            raise RuntimeError(
                "EmbeddingService not initialized. Call initialize() first."
            )
        vector: np.ndarray = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            raise RuntimeError(
                "EmbeddingService not initialized. Call initialize() first."
            )
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
        logger.info(
            "Building vector index from %d descriptions...",
            len(tool_descriptions),
        )
        ids, descriptions = zip(*tool_descriptions)
        vectors = self.embed_batch(list(descriptions))
        self._index.build(list(zip(ids, vectors)))
        logger.info("Vector index ready.")

    @property
    def index(self) -> VectorIndex:
        return self._index
