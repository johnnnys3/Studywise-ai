from __future__ import annotations

import re
from typing import Any


def extract_chunk_propositions(chunk: dict[str, Any], max_items: int = 5) -> list[dict[str, Any]]:
    propositions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sentence in _candidate_sentences(str(chunk.get("chunk_text", ""))):
        proposition = _normalize_sentence(sentence)
        if not _is_atomic_study_statement(proposition):
            continue
        key = proposition.lower()
        if key in seen:
            continue
        seen.add(key)
        propositions.append(
            {
                "user_id": chunk["user_id"],
                "document_id": chunk["document_id"],
                "chunk_id": chunk["id"],
                "page_number": chunk.get("page_number", chunk.get("page_start", 1)),
                "section_title": chunk.get("section_title"),
                "topic": _topic_from_statement(proposition),
                "statement": proposition,
                "content_type": _classify_statement(proposition, chunk.get("content_type")),
                "quality_score": _quality_score(proposition),
            }
        )
        if len(propositions) >= max_items:
            break
    return propositions


def _candidate_sentences(text: str) -> list[str]:
    candidates: list[str] = []
    for paragraph in re.split(r"\n+", text):
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            cleaned = _normalize_sentence(sentence)
            if cleaned:
                candidates.append(cleaned)
    return candidates


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence).strip(" -•\t")


def _is_atomic_study_statement(sentence: str) -> bool:
    words = sentence.split()
    if not 8 <= len(words) <= 45:
        return False
    if not any(char.isalpha() for char in sentence):
        return False
    lowered = sentence.lower()
    if lowered.startswith(("click ", "download ", "copyright ", "all rights reserved")):
        return False
    return bool(re.search(r"\b(is|are|means|refers|uses|requires|causes|helps|allows|improves|includes|consists|depends|leads)\b", lowered))


def _topic_from_statement(statement: str) -> str:
    stop_terms = {
        "which",
        "there",
        "their",
        "about",
        "because",
        "these",
        "those",
        "study",
        "material",
        "document",
    }
    for word in re.findall(r"[A-Za-z][A-Za-z-]{4,}", statement):
        if word.lower() not in stop_terms:
            return word.strip("-").title()
    return "Core Concepts"


def _classify_statement(statement: str, fallback: Any) -> str:
    lowered = statement.lower()
    if re.search(r"\b(means|refers to|is defined as|definition)\b", lowered):
        return "definition"
    if re.search(r"\b(because|therefore|causes|leads to|results in)\b", lowered):
        return "cause_effect"
    if re.search(r"\b(first|second|then|finally|process|step)\b", lowered):
        return "process"
    if re.search(r"\b(compared with|whereas|unlike|similar)\b", lowered):
        return "comparison"
    return str(fallback or "fact")


def _quality_score(statement: str) -> float:
    words = statement.split()
    length_score = min(len(words) / 18, 1.0)
    specificity = min(len(set(word.lower() for word in words)) / max(len(words), 1), 1.0)
    punctuation = 1.0 if statement.endswith((".", "!", "?")) else 0.75
    return round((length_score * 0.45) + (specificity * 0.4) + (punctuation * 0.15), 3)
