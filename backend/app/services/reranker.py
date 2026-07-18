from __future__ import annotations

import logging
from typing import Any


_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_logger = logging.getLogger(__name__)
_model: Any | None = None
_model_load_failed = False


def rerank(question: str, chunks: list[dict[str, Any]], top_n: int | None = None) -> list[dict[str, Any]] | None:
    """Cross-encoder rerank of candidate chunks against the question.

    Returns None (letting the caller fall back to heuristic scoring) if the
    cross-encoder model isn't available, so this stays optional infra like
    the sentence-transformers embedder in embeddings.py.
    """
    model = _get_model()
    if model is None or not chunks:
        return None

    pairs = [(question, chunk["chunk_text"]) for chunk in chunks]
    scores = model.predict(pairs)
    reranked = [
        {**chunk, "cross_encoder_score": round(float(score), 6)}
        for chunk, score in zip(chunks, scores)
    ]
    reranked.sort(key=lambda item: item["cross_encoder_score"], reverse=True)
    return reranked[:top_n] if top_n else reranked


def _get_model() -> Any | None:
    global _model, _model_load_failed
    if _model is not None:
        return _model
    if _model_load_failed:
        return None

    try:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(_MODEL_NAME)
        return _model
    except Exception:
        _model_load_failed = True
        _logger.warning(
            "Failed to load cross-encoder model %s; falling back to heuristic rerank.",
            _MODEL_NAME,
            exc_info=True,
        )
        return None
