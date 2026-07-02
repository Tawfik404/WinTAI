import numpy as np

from services.app_embeddings.index import AppIndex


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_best_match(
    query_embedding: list[float], index: AppIndex
) -> dict | None:
    if index.size == 0:
        return None

    query = np.array(query_embedding, dtype=np.float32)
    best_entry = None
    best_score = -1.0

    for entry in index.entries:
        sim = cosine_similarity(query, entry.embedding)
        if sim > best_score:
            best_score = sim
            best_entry = entry

    if best_entry is None:
        return None

    return {
        "name": best_entry.name,
        "path": best_entry.path,
        "source": best_entry.source,
        "confidence": round(best_score, 4),
    }
