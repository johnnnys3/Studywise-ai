# ADR 0001: Local sentence-transformers for RAG embeddings

- **Status:** Accepted
- **Date:** 2026-07-16
- **Context area:** Phase 3 RAG — `backend/app/services/embeddings.py`, `vector_store.py`

## Context

Phase 3's chunking (`chunker.py`), Chroma store with metadata filtering
(`vector_store.py`), and hybrid retrieval (`retriever.py`) are already built.
The remaining gap is `embeddings.py`: it produces a **deterministic hash-based
bag-of-words vector** (blake2b buckets, 384-dim), explicitly not semantic. As a
result, Chroma stores pseudo-random vectors and the vector arm of the hybrid
retriever contributes noise — carried only because keyword + proposition
ranking dominate the reciprocal-rank fusion.

Config already declares `openai_embedding_model: text-embedding-3-small`, but
`embeddings.py` ignores it.

## Decision

Replace the hash embedder with a real local embedding model.

1. **Provider:** local `sentence-transformers`, model `all-MiniLM-L6-v2`
   (384-dim). Chosen because it is already 384-dim (drops into the existing
   Chroma collection with no dimension migration), has no API key or per-request
   cost, and runs offline. Rejected: OpenAI `text-embedding-3-small` (1536-dim,
   forces collection reset, per-token cost, network in tests) and Gemini
   `text-embedding-004` (768-dim, API-gated).
2. **Fallback:** lazy-load the real model; on import/load failure, fall back to
   the existing hash embedder and log a one-time warning. Both are 384-dim so
   nothing downstream breaks; retrieval degrades to current behaviour rather
   than crashing. Rejected: hard-require the model (breaks torch-less
   environments and CI).
3. **Lifecycle:** module-level lazy singleton (load weights once). `embed_texts`
   does a real batch `model.encode(texts, normalize_embeddings=True)`;
   `embed_text` delegates to the batch path. Normalization done in-model so
   cosine works cleanly in Chroma.
4. **Existing data:** a one-off, idempotent reindex script
   (`backend/scripts/reindex_chroma.py`) deletes the Chroma collection and
   re-`upsert_document_chunks` from stored `document_chunks`. Embeddings are
   derived data (source chunks live in `store`), so wiping is safe and removes
   every fake vector. Rejected: lazy re-embed on next ingest only (leaves old
   docs silently poisoned).

## Consequences

- New dependency: `sentence-transformers` (+ torch) in `backend/requirements.txt`.
- `vector_store.py` and `retriever.py` need no changes — they already call
  `embed_texts` / `embed_text`.
- Ingest embeds synchronously inside the upload request; the first embed now
  blocks on a ~90MB model load. Accepted for MVP; revisit if upload latency
  matters.
- After deploy, run the reindex script once to purge pre-existing fake vectors.
