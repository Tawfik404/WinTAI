import logging

import numpy as np

from services.app_embeddings.model import EmbeddingModel
from services.app_embeddings.index import AppIndex, AppVector
from services.app_embeddings.search import find_best_match

logger = logging.getLogger(__name__)


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
        vectors = self._model.embed_batch(names)

        app_vectors: list[AppVector] = []
        for app, vec in zip(apps, vectors):
            try:
                app_vectors.append(
                    AppVector(
                        name=app["name"],
                        path=app.get("path", ""),
                        source=app.get("source", ""),
                        embedding=np.array(vec, dtype=np.float32),
                    )
                )
            except Exception:
                logger.warning("Skipping bad app entry: %s", app.get("name", "?"))
                continue

        self._index.build(app_vectors)
        self._initialized = True
        logger.info(
            "App embedding index ready: %d apps (dimension=%d)",
            self._index.size,
            self._model.get_dimension(),
        )

    def search(self, query: str) -> dict:
        if not self._initialized or self._index.size == 0:
            return {"name": "", "path": "", "source": "", "confidence": 0.0}

        query_vec = self._model.embed(query)
        result = find_best_match(query_vec, self._index)

        if result is None:
            return {"name": "", "path": "", "source": "", "confidence": 0.0}

        return result

    def get_index_size(self) -> int:
        return self._index.size
