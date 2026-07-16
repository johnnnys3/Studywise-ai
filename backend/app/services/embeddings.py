from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Any


EMBEDDING_DIMENSIONS = 384
_MODEL_NAME = "all-MiniLM-L6-v2"

_logger = logging.getLogger(__name__)
_model: Any | None = None
_model_load_failed = False


def embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    return embed_texts([text], dimensions)[0]


def embed_texts(texts: list[str], dimensions: int = EMBEDDING_DIMENSIONS) -> list[list[float]]:
    model = _get_model()
    if model is None:
        return [_fallback_embed_text(text, dimensions) for text in texts]

    vectors = model.encode(texts, normalize_embeddings=True)
    return [[round(float(value), 6) for value in vector] for vector in vectors]


def _get_model() -> Any | None:
    global _model, _model_load_failed
    if _model is not None:
        return _model
    if _model_load_failed:
        return None

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
        return _model
    except Exception:
        _model_load_failed = True
        _logger.warning(
            "Failed to load sentence-transformers model %s; falling back to hash-based embeddings.",
            _MODEL_NAME,
            exc_info=True,
        )
        return None


def _fallback_embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Deterministic local embedding fallback for Chroma and tests.

    This is not a replacement for a real embedding model, but it gives the MVP a
    stable semantic-ish vector path without adding dependencies or API keys.
    """
    vector = [0.0] * dimensions
    tokens = _tokens(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{1,}", text.lower())
    tokens: list[str] = []
    for token in raw_tokens:
        tokens.append(token)
        if "-" in token:
            tokens.extend(part for part in token.split("-") if part)
    return tokens
