from __future__ import annotations

import hashlib
import math
import re


EMBEDDING_DIMENSIONS = 384


def embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Deterministic local embedding fallback for Chroma and tests.

    This is not a replacement for OpenAI embeddings, but it gives the MVP a
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


def embed_texts(texts: list[str], dimensions: int = EMBEDDING_DIMENSIONS) -> list[list[float]]:
    return [embed_text(text, dimensions) for text in texts]


def _tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{1,}", text.lower())
    tokens: list[str] = []
    for token in raw_tokens:
        tokens.append(token)
        if "-" in token:
            tokens.extend(part for part in token.split("-") if part)
    return tokens
