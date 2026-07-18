import math
import re
from collections import Counter
from typing import Any, Iterator

from app.prompts.rag_prompts import RAG_ANSWER_SYSTEM_PROMPT
from app.services.llm_service import create_text_response, is_ai_configured, stream_text_response
from app.services.retriever import retrieve_chunks, tokenize
from app.storage import store


# How much a sentence's parent-chunk relevance (from retrieval ranking) can
# outweigh its raw keyword overlap when picking sentences for the local
# answer. Keyword overlap alone can't tell a topical match ("ribosomes")
# from a coincidental one ("cell...role"); chunk relevance can, since it
# already reflects the cross-encoder's semantic judgment.
CHUNK_RELEVANCE_WEIGHT = 3.0


def build_answer(user_id: str, document_id: str, question: str) -> dict[str, Any]:
    retrieved_chunks = retrieve_chunks(user_id, document_id, question)
    if not retrieved_chunks:
        answer = "I cannot find enough information in the uploaded document to answer that."
        citations: list[dict[str, Any]] = []
    else:
        query_terms = set(tokenize(question))
        selected_sentences = _compress_relevant_sentences(query_terms, retrieved_chunks)

        citations = _build_citations(retrieved_chunks)
        if is_ai_configured():
            try:
                answer = _build_ai_answer(question, retrieved_chunks)
            except Exception:
                answer = _build_local_answer(selected_sentences, retrieved_chunks)
        else:
            answer = _build_local_answer(selected_sentences, retrieved_chunks)

    user_message = store.insert(
        "chat_messages",
        {"user_id": user_id, "document_id": document_id, "role": "user", "content": question, "citations_json": []},
    )
    assistant_message = store.insert(
        "chat_messages",
        {"user_id": user_id, "document_id": document_id, "role": "assistant", "content": answer, "citations_json": citations},
    )
    return {
        "answer": answer,
        "citations": citations,
        "retrieved_context": retrieved_chunks,
        "messages": [user_message, assistant_message],
    }


def _build_local_answer(selected_sentences: list[str], retrieved_chunks: list[dict[str, Any]]) -> str:
    if not selected_sentences:
        selected_sentences = [retrieved_chunks[0]["chunk_text"][:600].strip()]
    source = _source_label(retrieved_chunks[0])
    return f"{' '.join(selected_sentences)} ({source})."


def _build_ai_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    return create_text_response(RAG_ANSWER_SYSTEM_PROMPT, _build_ai_user_input(question, retrieved_chunks))


def _build_ai_user_input(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    context = "\n\n".join(_format_context_block(chunk) for chunk in retrieved_chunks[:8])
    return (
        f"Student question:\n{question}\n\n"
        f"Retrieved context blocks:\n{context}\n\n"
        "Write a concise answer grounded in these blocks. If evidence conflicts, explain the conflict with citations."
    )


def stream_answer(user_id: str, document_id: str, question: str) -> Iterator[tuple[str, Any]]:
    """Yields ("citations", list), then ("delta", str) chunks, then ("done", dict)."""
    retrieved_chunks = retrieve_chunks(user_id, document_id, question)
    if not retrieved_chunks:
        answer = "I cannot find enough information in the uploaded document to answer that."
        citations: list[dict[str, Any]] = []
        yield ("citations", citations)
        yield ("delta", answer)
    else:
        citations = _build_citations(retrieved_chunks)
        yield ("citations", citations)
        answer = ""
        if is_ai_configured():
            try:
                for delta in stream_text_response(RAG_ANSWER_SYSTEM_PROMPT, _build_ai_user_input(question, retrieved_chunks)):
                    answer += delta
                    yield ("delta", delta)
            except Exception:
                answer = ""
        if not answer:
            query_terms = set(tokenize(question))
            selected_sentences = _compress_relevant_sentences(query_terms, retrieved_chunks)
            answer = _build_local_answer(selected_sentences, retrieved_chunks)
            yield ("delta", answer)

    user_message = store.insert(
        "chat_messages",
        {"user_id": user_id, "document_id": document_id, "role": "user", "content": question, "citations_json": []},
    )
    assistant_message = store.insert(
        "chat_messages",
        {"user_id": user_id, "document_id": document_id, "role": "assistant", "content": answer, "citations_json": citations},
    )
    yield ("done", {"messages": [user_message, assistant_message]})


def _build_citations(retrieved_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": chunk["document_id"],
            "chunk_id": chunk["id"],
            "page_number": chunk["page_number"],
            "page_start": chunk.get("page_start", chunk["page_number"]),
            "page_end": chunk.get("page_end", chunk["page_number"]),
            "chunk_index": chunk["chunk_index"],
            "section_title": chunk.get("section_title"),
            "source_label": _source_label(chunk),
        }
        for chunk in retrieved_chunks[:3]
    ]


def _format_context_block(chunk: dict[str, Any]) -> str:
    section = f"Section: {chunk.get('section_title')}\n" if chunk.get("section_title") else ""
    return (
        f"[{_source_label(chunk)} | source_chunk_id: {chunk['id']} | content_type: {chunk.get('content_type', 'paragraph')}]\n"
        f"{section}{_compress_chunk_text(chunk)}"
    )


def _split_sentences(text: str) -> list[str]:
    # Collapse whitespace first, including single line-wrap newlines from
    # PDF-extracted text, so a wrapped line doesn't get treated as a
    # sentence boundary and fragment a real sentence mid-clause.
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", normalized) if sentence.strip()]


def _compress_chunk_text(chunk: dict[str, Any], max_chars: int = 1800) -> str:
    text = str(chunk["chunk_text"]).strip()
    if len(text) <= max_chars:
        return text
    sentences = _split_sentences(text)
    kept: list[str] = []
    total = 0
    for sentence in sentences:
        if total + len(sentence) > max_chars:
            break
        kept.append(sentence)
        total += len(sentence)
    return " ".join(kept) if kept else text[:max_chars].strip()


def _compress_relevant_sentences(query_terms: set[str], retrieved_chunks: list[dict[str, Any]]) -> list[str]:
    if not retrieved_chunks:
        return []

    entries: list[tuple[str, list[str], float]] = []
    for chunk in retrieved_chunks:
        relevance = _chunk_relevance_signal(chunk)
        for sentence in _split_sentences(chunk["chunk_text"]):
            entries.append((sentence, tokenize(sentence), relevance))

    lowest = min(relevance for _, _, relevance in entries)
    highest = max(relevance for _, _, relevance in entries)
    spread = highest - lowest or 1.0

    document_frequency: Counter[str] = Counter()
    for _, tokens, _ in entries:
        document_frequency.update(set(tokens))
    total_sentences = len(entries)

    def idf(term: str) -> float:
        return math.log((total_sentences + 1) / (document_frequency[term] + 1)) + 1

    scored: list[tuple[float, str]] = []
    for sentence, tokens, relevance in entries:
        keyword_score = sum(idf(term) for term in query_terms.intersection(tokens))
        chunk_relevance = (relevance - lowest) / spread
        scored.append((keyword_score + chunk_relevance * CHUNK_RELEVANCE_WEIGHT, sentence))

    selected: list[str] = []
    for _, sentence in sorted(scored, key=lambda item: item[0], reverse=True):
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) >= 5:
            break
    return selected


def _chunk_relevance_signal(chunk: dict[str, Any]) -> float:
    if "cross_encoder_score" in chunk:
        return float(chunk["cross_encoder_score"])
    return float(chunk.get("score", 0.0))


def _source_label(chunk: dict[str, Any]) -> str:
    page_start = int(chunk.get("page_start", chunk.get("page_number", 1)))
    page_end = int(chunk.get("page_end", page_start))
    page_label = f"pages {page_start}-{page_end}" if page_end != page_start else f"page {page_start}"
    return f"{page_label}, chunk {int(chunk.get('chunk_index', 0)) + 1}"
