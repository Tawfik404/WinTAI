import logging

import numpy as np

logger = logging.getLogger(__name__)


class VectorIndex:
    def __init__(self) -> None:
        self._entries: list[tuple[str, np.ndarray]] = []

    def build(self, entries: list[tuple[str, list[float]]]) -> None:
        self._entries = [
            (tool_id, np.array(vector, dtype=np.float32)) for tool_id, vector in entries
        ]
        if self._entries:
            dim = self._entries[0][1].shape[0]
            logger.info(
                "Vector index built with %d entries (dimension=%d).",
                len(self._entries),
                dim,
            )

    def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[tuple[str, float]]:
        if not self._entries:
            return []

        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        scores: list[tuple[str, float]] = []
        for tool_id, vec in self._entries:
            sim = float(np.dot(query, vec) / (query_norm * np.linalg.norm(vec)))
            scores.append((tool_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def clear(self) -> None:
        self._entries.clear()

    def to_records(self) -> list[tuple[str, list[float]]]:
        return [(tool_id, vector.tolist()) for tool_id, vector in self._entries]

    def load_records(self, records: list[tuple[str, list[float]]]) -> None:
        self.build(records)

    @property
    def size(self) -> int:
        return len(self._entries)
