import re
from typing import Any

from app.prompts.rag_prompts import RAG_ANSWER_SYSTEM_PROMPT
from app.services.llm_service import create_text_response, is_ai_configured
from app.services.retriever import retrieve_chunks, tokenize
from app.storage import store


def build_answer(user_id: str, document_id: str, question: str) -> dict[str, Any]:
    retrieved_chunks = retrieve_chunks(user_id, document_id, question)
    if not retrieved_chunks:
        answer = "I cannot find enough information in the uploaded document to answer that."
        citations: list[dict[str, Any]] = []
    else:
        query_terms = set(tokenize(question))
        selected_sentences = _compress_relevant_sentences(query_terms, retrieved_chunks)

        citations = [
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
    context = "\n\n".join(_format_context_block(chunk) for chunk in retrieved_chunks[:8])
    user_input = (
        f"Student question:\n{question}\n\n"
        f"Retrieved context blocks:\n{context}\n\n"
        "Write a concise answer grounded in these blocks. If evidence conflicts, explain the conflict with citations."
    )
    return create_text_response(RAG_ANSWER_SYSTEM_PROMPT, user_input)


def _format_context_block(chunk: dict[str, Any]) -> str:
    section = f"Section: {chunk.get('section_title')}\n" if chunk.get("section_title") else ""
    return (
        f"[{_source_label(chunk)} | source_chunk_id: {chunk['id']} | content_type: {chunk.get('content_type', 'paragraph')}]\n"
        f"{section}{_compress_chunk_text(chunk)}"
    )


def _compress_chunk_text(chunk: dict[str, Any], max_chars: int = 1800) -> str:
    text = str(chunk["chunk_text"]).strip()
    if len(text) <= max_chars:
        return text
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    kept: list[str] = []
    total = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if total + len(sentence) > max_chars:
            break
        kept.append(sentence)
        total += len(sentence)
    return " ".join(kept) if kept else text[:max_chars].strip()


def _compress_relevant_sentences(query_terms: set[str], retrieved_chunks: list[dict[str, Any]]) -> list[str]:
    selected: list[str] = []
    for chunk in retrieved_chunks:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", chunk["chunk_text"])
        scored = [
            (len(query_terms.intersection(tokenize(sentence))), sentence.strip())
            for sentence in sentences
            if sentence.strip()
        ]
        for _, sentence in sorted(scored, key=lambda item: item[0], reverse=True):
            if sentence and sentence not in selected:
                selected.append(sentence)
            if len(selected) >= 5:
                return selected
    return selected


def _source_label(chunk: dict[str, Any]) -> str:
    page_start = int(chunk.get("page_start", chunk.get("page_number", 1)))
    page_end = int(chunk.get("page_end", page_start))
    page_label = f"pages {page_start}-{page_end}" if page_end != page_start else f"page {page_start}"
    return f"{page_label}, chunk {int(chunk.get('chunk_index', 0)) + 1}"
