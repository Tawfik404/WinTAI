from dataclasses import dataclass, field

import numpy as np


@dataclass
class AppVector:
    name: str
    path: str
    source: str
    embedding: np.ndarray
    alias_embeddings: list[np.ndarray] = field(default_factory=list)


class AppIndex:
    def __init__(self) -> None:
        self._entries: list[AppVector] = []

    def build(self, entries: list[AppVector]) -> None:
        self._entries = list(entries)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> list[AppVector]:
        return self._entries
