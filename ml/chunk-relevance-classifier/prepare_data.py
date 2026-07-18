"""Builds a labeled (question, chunk_text) -> relevant/not-relevant dataset
from StudyWise's own RAG traces (backend/data/studywise.json), and splits it
by question to avoid leakage.

Label source:
  - Positive (1): chunk was retrieved for the question and ranked in the
    top 2 results of the app's hybrid retriever (keyword + proposition +
    chroma), i.e. the retriever considered it a strong match.
  - Hard negative (0): chunk was retrieved for the question but ranked
    below the top 2 -- present in the candidate set but not strong enough.
  - Easy negative (0): chunk sampled from a document unrelated to the
    question's source document -- guaranteed irrelevant.

Usage (from repo root):
    /private/tmp/sw-venv/bin/python ml/chunk-relevance-classifier/prepare_data.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO_ROOT / "backend" / "data" / "studywise.json"
OUT_DIR = Path(__file__).resolve().parent / "data"

RANK_POSITIVE_CUTOFF = 2   # rank <= this (1-indexed) -> positive
EASY_NEGATIVES_PER_QUESTION = 6
RANDOM_SEED = 42


def load_source() -> dict:
    return json.loads(DATA_PATH.read_text())


def build_examples(source: dict, rng: random.Random) -> list[dict]:
    chunks_by_id = {c["id"]: c for c in source["document_chunks"]}
    chunks_by_doc: dict[str, list[dict]] = {}
    for chunk in source["document_chunks"]:
        chunks_by_doc.setdefault(chunk["document_id"], []).append(chunk)
    all_doc_ids = list(chunks_by_doc.keys())

    examples: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for trace in source["rag_traces"]:
        question = trace["question"]
        doc_id = trace["document_id"]
        results = sorted(trace["top_results_json"], key=lambda r: -r["score"])

        for rank, result in enumerate(results, start=1):
            chunk = chunks_by_id.get(result["chunk_id"])
            if chunk is None:
                continue
            key = (question, chunk["id"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            label = 1 if rank <= RANK_POSITIVE_CUTOFF else 0
            examples.append(
                {
                    "question": question,
                    "chunk_text": chunk["chunk_text"],
                    "label": label,
                    "source": "retrieved_rank",
                    "rank": rank,
                    "score": result["score"],
                }
            )

        other_doc_ids = [d for d in all_doc_ids if d != doc_id]
        if not other_doc_ids:
            continue
        candidate_negatives = [
            chunk
            for other_id in other_doc_ids
            for chunk in chunks_by_doc[other_id]
        ]
        rng.shuffle(candidate_negatives)
        for chunk in candidate_negatives[:EASY_NEGATIVES_PER_QUESTION]:
            key = (question, chunk["id"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            examples.append(
                {
                    "question": question,
                    "chunk_text": chunk["chunk_text"],
                    "label": 0,
                    "source": "cross_document",
                    "rank": None,
                    "score": None,
                }
            )

    return examples


def split_by_question(
    examples: list[dict], rng: random.Random, train_frac: float = 0.7, val_frac: float = 0.15
) -> dict[str, list[dict]]:
    questions = sorted({ex["question"] for ex in examples})
    rng.shuffle(questions)
    n = len(questions)
    n_train = max(1, round(n * train_frac))
    n_val = max(1, round(n * val_frac))
    train_qs = set(questions[:n_train])
    val_qs = set(questions[n_train : n_train + n_val])
    test_qs = set(questions[n_train + n_val :]) or set(questions[-1:])

    splits = {"train": [], "validation": [], "test": []}
    for ex in examples:
        if ex["question"] in train_qs:
            splits["train"].append(ex)
        elif ex["question"] in val_qs:
            splits["validation"].append(ex)
        else:
            splits["test"].append(ex)
    return splits


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    source = load_source()
    examples = build_examples(source, rng)
    rng.shuffle(examples)
    splits = split_by_question(examples, rng)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in splits.items():
        path = OUT_DIR / f"{name}.jsonl"
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    print(f"total examples: {len(examples)}")
    for name, rows in splits.items():
        pos = sum(1 for r in rows if r["label"] == 1)
        qs = len({r["question"] for r in rows})
        print(f"  {name:<12} n={len(rows):<4} positives={pos:<4} questions={qs}")


if __name__ == "__main__":
    main()
