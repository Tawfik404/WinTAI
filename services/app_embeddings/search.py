import logging

import numpy as np

from services.app_embeddings.index import AppIndex, AppVector

logger = logging.getLogger(__name__)

_SOURCE_PRIORITY: dict[str, int] = {
    "registry": 1,
    "start_menu": 2,
    "appx": 3,
    "desktop": 4,
    "program_files": 5,
}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _rerank_candidates(
    candidates: list[tuple[AppVector, float]], top_k: int = 5
) -> list[tuple[AppVector, float]]:
    """Rerank candidates: prefer higher similarity; within ±0.03 prefer better source."""
    if not candidates:
        return []

    candidates.sort(key=lambda x: -x[1])

    grouped: list[list[tuple[AppVector, float]]] = [[candidates[0]]]
    for item in candidates[1:]:
        if abs(grouped[-1][0][1] - item[1]) <= 0.03:
            grouped[-1].append(item)
        else:
            grouped.append([item])

    result: list[tuple[AppVector, float]] = []
    for group in grouped:
        group.sort(key=lambda x: _SOURCE_PRIORITY.get(x[0].source, 99))
        result.extend(group)

    return result[:top_k]


def find_top_k(
    query_embedding: list[float],
    index: AppIndex,
    top_k: int = 5,
) -> list[tuple[AppVector, float]]:
    """Return top-K (entry, score) after cosine similarity + reranking."""
    if index.size == 0:
        return []

    query = np.array(query_embedding, dtype=np.float32)
    scored: list[tuple[AppVector, float]] = []

    for entry in index.entries:
        best_score = cosine_similarity(query, entry.embedding)

        for alias_emb in entry.alias_embeddings:
            sim = cosine_similarity(query, alias_emb)
            if sim > best_score:
                best_score = sim

        scored.append((entry, best_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = _rerank_candidates(scored, top_k)

    logger.debug(
        "Top-%d candidates: %s",
        len(scored),
        [(e.name, round(s, 4)) for e, s in scored],
    )

    return scored


def find_best_match(
    query_embedding: list[float], index: AppIndex
) -> dict | None:
    ranked = find_top_k(query_embedding, index, top_k=5)
    if not ranked:
        return None

    best_entry, best_score = ranked[0]
    return {
        "name": best_entry.name,
        "path": best_entry.path,
        "source": best_entry.source,
        "confidence": round(best_score, 4),
    }
