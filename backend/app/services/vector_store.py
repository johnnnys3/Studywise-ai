from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.services.embeddings import embed_text, embed_texts


def upsert_document_chunks(chunks: list[dict[str, Any]]) -> None:
    collection = _collection()
    if collection is None or not chunks:
        return

    ids = [str(chunk["vector_id"]) for chunk in chunks]
    documents = [str(chunk["chunk_text"]) for chunk in chunks]
    embeddings = embed_texts(documents)
    metadatas = [_metadata(chunk) for chunk in chunks]
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def query_document_chunks(
    user_id: str,
    document_id: str,
    queries: list[str],
    top_k: int = 12,
    page_numbers: list[int] | None = None,
) -> list[dict[str, Any]]:
    collection = _collection()
    if collection is None:
        return []

    try:
        where_filter: dict[str, Any] = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}
        if page_numbers:
            where_filter["$and"].append({"page_number": {"$in": page_numbers}})
        result = collection.query(
            query_embeddings=[embed_text(query) for query in queries],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    hits: dict[str, dict[str, Any]] = {}
    ids_by_query = result.get("ids", [])
    metadatas_by_query = result.get("metadatas", [])
    documents_by_query = result.get("documents", [])
    distances_by_query = result.get("distances", [])
    for query_index, ids in enumerate(ids_by_query):
        for rank, vector_id in enumerate(ids):
            metadata = metadatas_by_query[query_index][rank] or {}
            distance = distances_by_query[query_index][rank]
            score = 1 / (1 + float(distance))
            current = hits.get(vector_id)
            if current and current["vector_score"] >= score:
                continue
            hits[vector_id] = {
                **metadata,
                "id": metadata.get("chunk_id"),
                "vector_id": vector_id,
                "chunk_text": documents_by_query[query_index][rank],
                "page_number": int(metadata.get("page_number", metadata.get("page_start", 1))),
                "page_start": int(metadata.get("page_start", metadata.get("page_number", 1))),
                "page_end": int(metadata.get("page_end", metadata.get("page_number", 1))),
                "chunk_index": int(metadata.get("chunk_index", 0)),
                "token_count": int(metadata.get("token_count", 0)),
                "vector_score": score,
                "retrieval_source": "chroma",
            }
    return sorted(hits.values(), key=lambda item: item["vector_score"], reverse=True)


def delete_document_chunks(user_id: str, document_id: str) -> None:
    collection = _collection()
    if collection is None:
        return
    try:
        collection.delete(where={"$and": [{"user_id": user_id}, {"document_id": document_id}]})
    except Exception:
        pass


def _collection() -> Any | None:
    settings = get_settings()
    if not settings.chroma_enabled:
        return None
    try:
        import chromadb
    except Exception:
        return None

    try:
        client = chromadb.PersistentClient(path=str(settings.chroma_path))
        return client.get_or_create_collection(name=settings.chroma_collection)
    except Exception:
        return None


def _metadata(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    section_path = chunk.get("section_path_json") or chunk.get("section_path") or []
    if isinstance(section_path, list):
        section_path_text = " > ".join(str(item) for item in section_path)
    else:
        section_path_text = str(section_path)
    return {
        "chunk_id": str(chunk["id"]),
        "user_id": str(chunk["user_id"]),
        "document_id": str(chunk["document_id"]),
        "chunk_index": int(chunk.get("chunk_index", 0)),
        "page_number": int(chunk.get("page_number", chunk.get("page_start", 1))),
        "page_start": int(chunk.get("page_start", chunk.get("page_number", 1))),
        "page_end": int(chunk.get("page_end", chunk.get("page_number", 1))),
        "section_title": str(chunk.get("section_title") or ""),
        "section_path": section_path_text,
        "content_type": str(chunk.get("content_type") or "paragraph"),
        "token_count": int(chunk.get("token_count", 0)),
        "quality_score": float(chunk.get("quality_score", 0.0)),
        "text_hash": str(chunk.get("text_hash") or ""),
    }
