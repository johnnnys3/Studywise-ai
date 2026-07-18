from __future__ import annotations

import logging
from typing import Any


_MODEL_NAME = "Johnnnys3/studywise-chunk-relevance-classifier"
_RELEVANT_LABEL = "relevant"

_logger = logging.getLogger(__name__)
_model: Any | None = None
_tokenizer: Any | None = None
_model_load_failed = False


def classify_relevance(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Scores each chunk's probability of being relevant to the question.

    Returns None (letting the caller skip this signal) if the classifier
    isn't available, matching the optional-infra pattern in reranker.py and
    embeddings.py.
    """
    model, tokenizer = _get_model()
    if model is None or tokenizer is None or not chunks:
        return None

    import torch

    relevant_index = model.config.label2id.get(_RELEVANT_LABEL)
    if relevant_index is None:
        return None

    scored = []
    with torch.no_grad():
        for chunk in chunks:
            inputs = tokenizer(
                question, chunk["chunk_text"], return_tensors="pt", truncation=True, max_length=256
            )
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            scored.append({**chunk, "relevance_score": round(float(probs[relevant_index]), 6)})
    return scored


def _get_model() -> tuple[Any | None, Any | None]:
    global _model, _tokenizer, _model_load_failed
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer
    if _model_load_failed:
        return None, None

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        _model.eval()
        return _model, _tokenizer
    except Exception:
        _model_load_failed = True
        _logger.warning(
            "Failed to load chunk relevance classifier %s; skipping relevance signal.",
            _MODEL_NAME,
            exc_info=True,
        )
        return None, None
