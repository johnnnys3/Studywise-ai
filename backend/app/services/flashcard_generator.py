from typing import Any

from app.storage import store


def generate_flashcards(user_id: str, document_id: str, count: int = 6) -> list[dict[str, Any]]:
    existing = store.filter("flashcards", user_id=user_id, document_id=document_id)
    if existing:
        return existing

    chunks = sorted(
        store.filter("document_chunks", user_id=user_id, document_id=document_id),
        key=lambda chunk: (-float(chunk.get("quality_score", 0)), int(chunk.get("chunk_index", 0))),
    )
    cards: list[dict[str, Any]] = []
    for chunk in chunks[:count]:
        text = chunk["chunk_text"]
        topic = chunk.get("section_title") or "Document Review"
        front = f"What should you remember about {topic} from page {chunk['page_number']}?"
        back = text[:360].strip()
        cards.append(
            store.insert(
                "flashcards",
                {
                    "user_id": user_id,
                    "document_id": document_id,
                    "front": front,
                    "back": back,
                    "topic": topic,
                    "source_page": chunk["page_number"],
                    "source_chunk_id": chunk.get("id"),
                    "difficulty": "medium" if chunk.get("content_type") in {"process", "example"} else "easy",
                },
            )
        )
    return cards
