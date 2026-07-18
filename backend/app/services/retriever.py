import math
import re
from collections import Counter
from typing import Any

from app.services.chunk_relevance_classifier import classify_relevance
from app.services.llm_service import create_structured_response, is_ai_configured
from app.services.reranker import rerank as cross_encoder_rerank
from app.services.vector_store import query_document_chunks
from app.storage import store


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when",
    "where", "which", "who", "why", "with",
}


def tokenize(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-zA-Z0-9]+", text.lower()) if word not in STOP_WORDS]


def score_chunk(question_tokens: Counter[str], chunk_text: str) -> float:
    chunk_tokens = Counter(tokenize(chunk_text))
    if not question_tokens or not chunk_tokens:
        return 0.0
    overlap = sum(min(count, chunk_tokens[token]) for token, count in question_tokens.items())
    density = overlap / math.sqrt(sum(chunk_tokens.values()))
    coverage = overlap / max(sum(question_tokens.values()), 1)
    return density + coverage + (0.2 if overlap else 0)


def retrieve_chunks(user_id: str, document_id: str, question: str, top_k: int = 8) -> list[dict[str, Any]]:
    queries = rewrite_query(question)
    page_filter = _extract_page_filter(question)
    chunks = _filtered_chunks(user_id, document_id, page_filter)
    if not chunks:
        return []

    keyword_ranked = _keyword_retrieve(chunks, queries, limit=max(top_k * 3, 20))
    proposition_ranked = _proposition_retrieve(user_id, document_id, queries, chunks, page_filter, limit=max(top_k * 3, 20))
    vector_ranked = _vector_retrieve(user_id, document_id, queries, chunks, limit=max(top_k * 3, 20), page_filter=page_filter)
    fused = _reciprocal_rank_fusion([keyword_ranked, proposition_ranked, vector_ranked])
    deduped = _dedupe(fused)
    reranked = _rerank(question, deduped)
    _record_retrieval_trace(user_id, document_id, question, queries, reranked, page_filter)
    results = reranked[: min(top_k, len(reranked))]
    if _is_out_of_scope(results):
        return []
    return results


# Cross-encoder logits below this are treated as "not actually about the
# question" rather than merely low-ranked, so the caller can refuse instead
# of answering from irrelevant chunks. Only applied when the cross-encoder
# loaded; without it there's no calibrated signal to gate on.
RELEVANCE_THRESHOLD = -5.0


def _is_out_of_scope(chunks: list[dict[str, Any]]) -> bool:
    if not chunks:
        return False
    top_score = chunks[0].get("cross_encoder_score")
    if top_score is None:
        return False
    return float(top_score) < RELEVANCE_THRESHOLD


def rewrite_query(question: str) -> list[str]:
    local_queries = _local_query_rewrites(question)
    if not is_ai_configured():
        return local_queries

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["queries"],
        "properties": {
            "queries": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {"type": "string"},
            }
        },
    }
    try:
        response = create_structured_response(
            "Rewrite the student question into retrieval queries only. Do not answer it.",
            f"Question: {question}\nReturn one semantic query, one keyword query, and one expanded query.",
            "studywise_query_rewrites",
            schema,
        )
    except Exception:
        return local_queries

    ai_queries = [str(query).strip() for query in response.get("queries", []) if str(query).strip()]
    return _unique([question, *ai_queries, *local_queries])[:4]


def _local_query_rewrites(question: str) -> list[str]:
    tokens = tokenize(question)
    keyword_query = " ".join(tokens[:12])
    subqueries = _decompose_question(question)
    step_back_query = _step_back_query(tokens)
    hypothetical_query = _hypothetical_answer_query(question, tokens)
    expanded_terms = []
    for token in tokens:
        expanded_terms.append(token)
        if token.endswith("s"):
            expanded_terms.append(token[:-1])
        if token.endswith("ing"):
            expanded_terms.append(token[:-3])
    return _unique([question, *subqueries, keyword_query, " ".join(expanded_terms), step_back_query, hypothetical_query])


def _keyword_retrieve(chunks: list[dict[str, Any]], queries: list[str], limit: int) -> list[dict[str, Any]]:
    ranked: dict[str, dict[str, Any]] = {}
    for query in queries:
        question_tokens = Counter(tokenize(query))
        for chunk in chunks:
            lexical_score = score_chunk(question_tokens, chunk["chunk_text"])
            heading_bonus = _heading_bonus(question_tokens, chunk)
            quality_bonus = min(float(chunk.get("quality_score", 0.0)), 1.0) * 0.05
            score = lexical_score + heading_bonus + quality_bonus
            current = ranked.get(chunk["id"])
            if current and current["keyword_score"] >= score:
                continue
            ranked[chunk["id"]] = {**chunk, "keyword_score": score, "retrieval_source": "keyword"}
    return sorted(ranked.values(), key=lambda item: item["keyword_score"], reverse=True)[:limit]


def _vector_retrieve(
    user_id: str,
    document_id: str,
    queries: list[str],
    stored_chunks: list[dict[str, Any]],
    limit: int,
    page_filter: list[int] | None = None,
) -> list[dict[str, Any]]:
    by_id = {chunk["id"]: chunk for chunk in stored_chunks}
    hits = []
    for hit in query_document_chunks(user_id, document_id, queries, top_k=limit, page_numbers=page_filter):
        stored = by_id.get(str(hit.get("id")))
        if stored:
            hits.append({**stored, "vector_score": hit.get("vector_score", 0), "retrieval_source": "chroma"})
    return sorted(hits, key=lambda item: item.get("vector_score", 0), reverse=True)[:limit]


def _proposition_retrieve(
    user_id: str,
    document_id: str,
    queries: list[str],
    chunks: list[dict[str, Any]],
    page_filter: list[int] | None,
    limit: int,
) -> list[dict[str, Any]]:
    chunk_by_id = {chunk["id"]: chunk for chunk in chunks}
    propositions = store.filter("chunk_propositions", user_id=user_id, document_id=document_id)
    if page_filter:
        propositions = [item for item in propositions if int(item.get("page_number", 0)) in page_filter]

    ranked: dict[str, dict[str, Any]] = {}
    for query in queries:
        query_tokens = Counter(tokenize(query))
        for proposition in propositions:
            chunk = chunk_by_id.get(str(proposition.get("chunk_id")))
            if not chunk:
                continue
            statement = str(proposition.get("statement", ""))
            score = score_chunk(query_tokens, statement)
            score += min(float(proposition.get("quality_score", 0.0)), 1.0) * 0.08
            if score <= 0:
                continue
            current = ranked.get(chunk["id"])
            if current and current["proposition_score"] >= score:
                continue
            ranked[chunk["id"]] = {
                **chunk,
                "proposition_score": score,
                "matched_proposition": statement,
                "retrieval_source": "proposition",
            }
    return sorted(ranked.values(), key=lambda item: item["proposition_score"], reverse=True)[:limit]


def _reciprocal_rank_fusion(rankings: list[list[dict[str, Any]]], k: int = 60) -> list[dict[str, Any]]:
    fused: dict[str, dict[str, Any]] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, start=1):
            chunk_id = chunk["id"]
            current = fused.setdefault(chunk_id, {**chunk, "score": 0.0, "retrieval_sources": []})
            current["score"] += 1 / (k + rank)
            source = chunk.get("retrieval_source", "unknown")
            if source not in current["retrieval_sources"]:
                current["retrieval_sources"].append(source)
            current["keyword_score"] = max(float(current.get("keyword_score", 0)), float(chunk.get("keyword_score", 0)))
            current["vector_score"] = max(float(current.get("vector_score", 0)), float(chunk.get("vector_score", 0)))
            current["proposition_score"] = max(float(current.get("proposition_score", 0)), float(chunk.get("proposition_score", 0)))
            if chunk.get("matched_proposition"):
                current["matched_proposition"] = chunk["matched_proposition"]
    return sorted(fused.values(), key=lambda item: item["score"], reverse=True)


def _dedupe(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    seen_texts: set[str] = set()
    for chunk in chunks:
        text_hash = str(chunk.get("text_hash") or "")
        normalized = re.sub(r"\s+", " ", chunk["chunk_text"].lower()).strip()[:300]
        if text_hash and text_hash in seen_hashes:
            continue
        if normalized in seen_texts:
            continue
        if text_hash:
            seen_hashes.add(text_hash)
        seen_texts.add(normalized)
        deduped.append(chunk)
    return deduped


CROSS_ENCODER_CANDIDATES = 30


def _rerank(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    question_tokens = Counter(tokenize(question))
    reranked = []
    for chunk in chunks:
        support_score = _support_density(question_tokens, chunk["chunk_text"])
        content_bonus = 0.04 if chunk.get("content_type") in {"definition", "example", "process"} else 0.0
        proposition_bonus = min(float(chunk.get("proposition_score", 0)), 1.0) * 0.18
        score = float(chunk.get("score", 0)) + support_score + content_bonus + proposition_bonus
        reranked.append({**chunk, "score": round(score, 6), "support_score": round(support_score, 6)})
    reranked.sort(key=lambda item: item["score"], reverse=True)
    return _apply_relevance_classifier(question, _apply_cross_encoder(question, reranked))


def _apply_cross_encoder(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = chunks[:CROSS_ENCODER_CANDIDATES]
    scored = cross_encoder_rerank(question, candidates)
    if not scored:
        return chunks

    ce_scores = [chunk["cross_encoder_score"] for chunk in scored]
    lowest, highest = min(ce_scores), max(ce_scores)
    spread = highest - lowest or 1.0
    by_id = {chunk["id"]: chunk for chunk in scored}

    blended = []
    for chunk in chunks:
        ce_chunk = by_id.get(chunk["id"])
        if ce_chunk is None:
            blended.append(chunk)
            continue
        normalized_ce = (ce_chunk["cross_encoder_score"] - lowest) / spread
        score = float(chunk["score"]) * 0.4 + normalized_ce * 0.6
        blended.append({**chunk, "score": round(score, 6), "cross_encoder_score": ce_chunk["cross_encoder_score"]})
    return sorted(blended, key=lambda item: item["score"], reverse=True)


# Small blend weight -- the classifier trails a majority-class baseline on
# raw accuracy (see ml/chunk-relevance-classifier/model_card.md), so it acts
# as a mild nudge on top of the cross-encoder rather than a strong signal.
RELEVANCE_CLASSIFIER_WEIGHT = 0.15
RELEVANCE_CLASSIFIER_CANDIDATES = 30


def _apply_relevance_classifier(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = chunks[:RELEVANCE_CLASSIFIER_CANDIDATES]
    scored = classify_relevance(question, candidates)
    if not scored:
        return chunks

    by_id = {chunk["id"]: chunk for chunk in scored}
    blended = []
    for chunk in chunks:
        scored_chunk = by_id.get(chunk["id"])
        if scored_chunk is None:
            blended.append(chunk)
            continue
        relevance_score = scored_chunk["relevance_score"]
        score = float(chunk["score"]) * (1 - RELEVANCE_CLASSIFIER_WEIGHT) + relevance_score * RELEVANCE_CLASSIFIER_WEIGHT
        blended.append({**chunk, "score": round(score, 6), "relevance_score": relevance_score})
    return sorted(blended, key=lambda item: item["score"], reverse=True)


def _filtered_chunks(user_id: str, document_id: str, page_filter: list[int] | None) -> list[dict[str, Any]]:
    chunks = store.filter("document_chunks", user_id=user_id, document_id=document_id)
    if not page_filter:
        return chunks
    return [
        chunk
        for chunk in chunks
        if int(chunk.get("page_start", chunk.get("page_number", 1))) <= max(page_filter)
        and int(chunk.get("page_end", chunk.get("page_number", 1))) >= min(page_filter)
    ]


def _extract_page_filter(question: str) -> list[int] | None:
    pages: set[int] = set()
    for match in re.finditer(r"\bpages?\s+(\d+)(?:\s*[-–]\s*(\d+))?", question.lower()):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start > end or end - start > 10:
            continue
        pages.update(range(start, end + 1))
    return sorted(pages) if pages else None


def _decompose_question(question: str) -> list[str]:
    parts = [
        part.strip(" ?.")
        for part in re.split(r"\b(?:and|versus|vs\.?|compared with|compare|while)\b|[;:]", question, flags=re.IGNORECASE)
    ]
    return [part for part in parts if len(tokenize(part)) >= 3][:3]


def _step_back_query(tokens: list[str]) -> str:
    if not tokens:
        return ""
    return " ".join(tokens[:8] + ["definition", "purpose", "relationship"])


def _hypothetical_answer_query(question: str, tokens: list[str]) -> str:
    if not tokens:
        return question
    if question.lower().startswith(("why", "how")):
        return " ".join(tokens[:10] + ["because", "process", "reason", "effect"])
    if "compare" in question.lower() or "difference" in question.lower():
        return " ".join(tokens[:10] + ["similarity", "difference", "whereas"])
    return " ".join(tokens[:10] + ["means", "refers", "includes"])


def _record_retrieval_trace(
    user_id: str,
    document_id: str,
    question: str,
    queries: list[str],
    results: list[dict[str, Any]],
    page_filter: list[int] | None,
) -> None:
    top_results = [
        {
            "chunk_id": result["id"],
            "score": result.get("score", 0),
            "page_number": result.get("page_number"),
            "sources": result.get("retrieval_sources", []),
            "matched_proposition": result.get("matched_proposition"),
        }
        for result in results[:8]
    ]
    store.insert(
        "rag_traces",
        {
            "user_id": user_id,
            "document_id": document_id,
            "question": question,
            "rewritten_queries_json": queries,
            "page_filter_json": page_filter or [],
            "top_results_json": top_results,
            "retrieval_top_k": len(results),
        },
    )


def _support_density(question_tokens: Counter[str], text: str) -> float:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    if not sentences:
        return 0.0
    best = 0.0
    for sentence in sentences:
        best = max(best, score_chunk(question_tokens, sentence))
    return best * 0.45


def _heading_bonus(question_tokens: Counter[str], chunk: dict[str, Any]) -> float:
    heading_text = " ".join(
        str(value or "")
        for value in [chunk.get("section_title"), " ".join(chunk.get("section_path_json") or [])]
    )
    heading_tokens = Counter(tokenize(heading_text))
    if not heading_tokens:
        return 0.0
    overlap = sum(min(count, heading_tokens[token]) for token, count in question_tokens.items())
    return min(overlap * 0.08, 0.3)


def _unique(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = re.sub(r"\s+", " ", item).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique_items.append(normalized)
    return unique_items
