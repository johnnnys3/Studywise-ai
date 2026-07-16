"""Idempotent Chroma reindex: wipe the collection and re-embed from stored document_chunks.

Run after switching the embedding model so old (e.g. hash-based) vectors don't
linger alongside real ones. Source chunks are derived data's source of truth
lives in app.storage.store, so deleting the collection first is safe.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.storage import store
from app.services.vector_store import upsert_document_chunks


def reindex() -> None:
    settings = get_settings()
    if not settings.chroma_enabled:
        print("Chroma is disabled (CHROMA_ENABLED=false); nothing to reindex.")
        return

    import chromadb

    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    try:
        client.delete_collection(name=settings.chroma_collection)
    except Exception:
        pass

    chunks = store.all("document_chunks")
    if not chunks:
        print("No document_chunks found; collection reset with nothing to re-embed.")
        return

    upsert_document_chunks(chunks)
    print(f"Re-embedded {len(chunks)} document chunks into '{settings.chroma_collection}'.")


if __name__ == "__main__":
    reindex()
