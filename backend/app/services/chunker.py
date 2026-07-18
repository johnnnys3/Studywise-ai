from dataclasses import dataclass
import hashlib
import re
from typing import Any


@dataclass
class TextChunk:
    chunk_index: int
    chunk_text: str
    page_number: int
    token_count: int
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    section_path: list[str] | None = None
    content_type: str = "paragraph"
    quality_score: float = 0.0
    text_hash: str = ""


def chunk_text(text: str, page_number: int = 1, chunk_size: int = 650, overlap: int = 125) -> list[TextChunk]:
    chunks = semantic_chunk_pages(
        [{"page_number": page_number, "text": text}],
        chunk_size=chunk_size,
        overlap=overlap,
    )
    for index, chunk in enumerate(chunks):
        chunk.chunk_index = index
    return chunks


def semantic_chunk_pages(
    pages: list[dict[str, Any]],
    chunk_size: int = 650,
    overlap: int = 125,
) -> list[TextChunk]:
    """Chunk by document structure first, with word-window fallback for long sections."""
    blocks = _page_blocks(pages)
    if not blocks:
        return []

    chunks: list[TextChunk] = []
    section_path: list[str] = []
    buffer: list[dict[str, Any]] = []
    buffer_tokens = 0

    for block in blocks:
        if _looks_like_heading(block["text"]):
            if buffer:
                chunks.extend(_flush_buffer(buffer, section_path, chunk_size, overlap))
                buffer = []
                buffer_tokens = 0
            heading = _normalize_heading(block["text"])
            section_path = _update_section_path(section_path, heading)
            continue

        token_count = _token_count(block["text"])
        if token_count > chunk_size:
            if buffer:
                chunks.extend(_flush_buffer(buffer, section_path, chunk_size, overlap))
                buffer = []
                buffer_tokens = 0
            chunks.extend(_window_chunk_block(block, section_path, chunk_size, overlap))
            continue

        if buffer and buffer_tokens + token_count > chunk_size:
            chunks.extend(_flush_buffer(buffer, section_path, chunk_size, overlap))
            buffer = _overlap_blocks(buffer, overlap)
            buffer_tokens = sum(_token_count(item["text"]) for item in buffer)

        buffer.append(block)
        buffer_tokens += token_count

    if buffer:
        chunks.extend(_flush_buffer(buffer, section_path, chunk_size, overlap))

    deduped: list[TextChunk] = []
    seen_hashes: set[str] = set()
    for index, chunk in enumerate(chunks):
        if chunk.text_hash in seen_hashes or chunk.quality_score < 0.25:
            continue
        seen_hashes.add(chunk.text_hash)
        chunk.chunk_index = index
        deduped.append(chunk)
    return deduped


def _page_blocks(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for page in pages:
        page_number = int(page.get("page_number", 1))
        text = str(page.get("text", ""))
        for paragraph in re.split(r"\n{2,}", text):
            cleaned = re.sub(r"[ \t]+", " ", paragraph).strip()
            if cleaned:
                blocks.append(
                    {
                        "text": cleaned,
                        "page_start": page_number,
                        "page_end": page_number,
                        "content_type": _classify_content(cleaned),
                    }
                )
    return blocks


def _flush_buffer(
    blocks: list[dict[str, Any]],
    section_path: list[str],
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    text = "\n\n".join(block["text"] for block in blocks).strip()
    if _token_count(text) > chunk_size:
        block = {
            "text": text,
            "page_start": min(int(item["page_start"]) for item in blocks),
            "page_end": max(int(item["page_end"]) for item in blocks),
            "content_type": _dominant_content_type(blocks),
        }
        return _window_chunk_block(block, section_path, chunk_size, overlap)
    return [_make_chunk(blocks, section_path)]


def _window_chunk_block(
    block: dict[str, Any],
    section_path: list[str],
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    words = re.findall(r"\S+", block["text"])
    chunks: list[TextChunk] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        if chunk_words:
            chunk_text_value = " ".join(chunk_words)
            chunk = _make_chunk(
                [
                    {
                        "text": chunk_text_value,
                        "page_start": block["page_start"],
                        "page_end": block["page_end"],
                        "content_type": block.get("content_type", "paragraph"),
                    }
                ],
                section_path,
            )
            chunks.append(chunk)
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _make_chunk(blocks: list[dict[str, Any]], section_path: list[str]) -> TextChunk:
    text = "\n\n".join(block["text"] for block in blocks).strip()
    page_start = min(int(block["page_start"]) for block in blocks)
    page_end = max(int(block["page_end"]) for block in blocks)
    return TextChunk(
        chunk_index=0,
        chunk_text=text,
        page_number=page_start,
        page_start=page_start,
        page_end=page_end,
        token_count=_token_count(text),
        section_title=section_path[-1] if section_path else None,
        section_path=list(section_path),
        content_type=_dominant_content_type(blocks),
        quality_score=_quality_score(text),
        text_hash=_hash_text(text),
    )


def _overlap_blocks(blocks: list[dict[str, Any]], overlap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    token_total = 0
    for block in reversed(blocks):
        selected.insert(0, block)
        token_total += _token_count(block["text"])
        if token_total >= overlap:
            break
    return selected


def _looks_like_heading(text: str) -> bool:
    normalized = text.strip()
    if normalized.startswith(("•", "◦", "‣", "➢", "-", "*")):
        return False
    words = normalized.split()
    if not 1 <= len(words) <= 12:
        return False
    if normalized.endswith("."):
        return False
    if re.match(r"^(\d+(\.\d+)*|[A-Z])[\).:-]?\s+[A-Z]", normalized):
        return True
    alpha = [char for char in normalized if char.isalpha()]
    if alpha and sum(char.isupper() for char in alpha) / len(alpha) > 0.7:
        return True
    if normalized.istitle() and len(words) <= 8:
        return True
    if len(words) <= 6 and not re.search(r"[.,;:!?]", normalized):
        return not _looks_like_prose_fragment(words)
    return False


# Auxiliary/copula verbs and trailing conjunctions/prepositions that mark a
# short lowercase line as a mid-sentence prose fragment (e.g. from a PDF
# where each verse or wrapped line is its own paragraph) rather than a
# genuine standalone heading like "results and discussion".
_AUXILIARY_VERBS = {
    "is", "are", "was", "were", "am", "be", "been", "being",
    "has", "have", "had", "do", "does", "did",
    "will", "would", "can", "could", "shall", "should", "may", "might", "must",
}
_LEADING_OR_TRAILING_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "as", "if", "so", "because",
    "of", "in", "on", "at", "to", "with", "for", "from", "by",
}
_PRONOUNS = {
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "this", "that", "these", "those",
}


def _looks_like_prose_fragment(words: list[str]) -> bool:
    cleaned = [word.strip("()\"'.,:;").lower() for word in words]
    if not cleaned:
        return False
    if any(word in _AUXILIARY_VERBS or word in _PRONOUNS for word in cleaned):
        return True
    return cleaned[0] in _LEADING_OR_TRAILING_STOPWORDS or cleaned[-1] in _LEADING_OR_TRAILING_STOPWORDS


def _normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" :-")


def _update_section_path(current: list[str], heading: str) -> list[str]:
    level = 1
    match = re.match(r"^(\d+(?:\.\d+)*)", heading)
    if match:
        level = min(match.group(1).count(".") + 1, 4)
    elif len(heading.split()) <= 4:
        level = min(len(current) + 1, 3)
    return [*current[: level - 1], heading]


def _classify_content(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(is defined as|refers to|means|definition)\b", lowered):
        return "definition"
    if re.search(r"\b(for example|e\.g\.|example)\b", lowered):
        return "example"
    if re.search(r"\b(first|second|third|finally|step|process)\b", lowered):
        return "process"
    if "|" in text or re.search(r"\b(table|column|row)\b", lowered):
        return "table"
    return "paragraph"


def _dominant_content_type(blocks: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for block in blocks:
        content_type = str(block.get("content_type", "paragraph"))
        counts[content_type] = counts.get(content_type, 0) + 1
    return max(counts, key=counts.get) if counts else "paragraph"


def _quality_score(text: str) -> float:
    words = re.findall(r"[A-Za-z0-9]+", text)
    if not words:
        return 0.0
    alpha_chars = sum(char.isalpha() for char in text)
    visible_chars = max(sum(not char.isspace() for char in text), 1)
    length_score = min(len(words) / 80, 1.0)
    alpha_score = alpha_chars / visible_chars
    sentence_score = 1.0 if re.search(r"[.!?:;]", text) else 0.65
    return round(max(0.0, min((length_score * 0.45) + (alpha_score * 0.4) + (sentence_score * 0.15), 1.0)), 3)


def _hash_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))
