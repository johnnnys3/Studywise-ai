"""Runs the RAG eval set (tests/fixtures/rag_eval_set.json) against the live
retrieval + generation pipeline and reports quality metrics.

Usage (from backend/):
    python scripts/rag_eval.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(FIXTURES_DIR))

REFUSAL_MARKER = "cannot find enough information"


def load_eval_set() -> list[dict[str, Any]]:
    return json.loads((FIXTURES_DIR / "rag_eval_set.json").read_text())


def run_eval(client, headers: dict[str, str], document_id: str) -> dict[str, Any]:
    eval_set = load_eval_set()
    rows: list[dict[str, Any]] = []

    for case in eval_set:
        started = time.perf_counter()
        response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": case["question"]},
            headers=headers,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        payload = response.json()
        answer = str(payload.get("answer", "")).lower()
        citations = payload.get("citations", [])
        retrieved_pages = {chunk.get("page_number") for chunk in payload.get("retrieved_context", [])}

        row: dict[str, Any] = {
            "id": case["id"],
            "question": case["question"],
            "answerable": case["answerable"],
            "response_time_ms": round(elapsed_ms, 1),
            "refused": REFUSAL_MARKER in answer,
        }

        if case["answerable"]:
            row["chunk_retrieved"] = case["expected_page"] in retrieved_pages
            row["citation_present"] = bool(citations) if case["citation_required"] else True
            row["grounded"] = all(keyword in answer for keyword in case["expected_keywords"])
        else:
            row["chunk_retrieved"] = None
            row["citation_present"] = not citations
            row["grounded"] = row["refused"]

        rows.append(row)

    answerable_rows = [row for row in rows if row["answerable"]]
    unanswerable_rows = [row for row in rows if not row["answerable"]]

    def rate(items: list[dict[str, Any]], key: str) -> float:
        return round(sum(1 for item in items if item[key]) / len(items), 3) if items else 0.0

    metrics = {
        "retrieval_accuracy": rate(answerable_rows, "chunk_retrieved"),
        "citation_coverage": rate(answerable_rows, "citation_present"),
        "answer_groundedness": rate(answerable_rows, "grounded"),
        "refusal_accuracy": rate(unanswerable_rows, "refused"),
        "average_response_time_ms": round(
            sum(row["response_time_ms"] for row in rows) / len(rows), 1
        ) if rows else 0.0,
    }
    return {"rows": rows, "metrics": metrics}


def _print_report(result: dict[str, Any]) -> None:
    print(f"{'id':<26} {'retrieved':<10} {'cited':<8} {'grounded':<9} {'ms':>8}")
    for row in result["rows"]:
        print(
            f"{row['id']:<26} "
            f"{str(row['chunk_retrieved']):<10} "
            f"{str(row['citation_present']):<8} "
            f"{str(row['grounded']):<9} "
            f"{row['response_time_ms']:>8}"
        )
    print()
    for name, value in result["metrics"].items():
        print(f"{name}: {value}")


def main() -> None:
    from uuid import uuid4

    from fastapi.testclient import TestClient

    from app.main import app
    from eval_document import write_eval_pdf

    client = TestClient(app)
    suffix = uuid4().hex
    register = client.post(
        "/api/v1/auth/register",
        json={"name": f"Eval User {suffix}", "email": f"rag-eval-{suffix}@example.com", "password": "Password123!"},
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pdf_path = Path("/tmp") / f"rag_eval_{suffix}.pdf"
    write_eval_pdf(pdf_path)
    with pdf_path.open("rb") as file:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("eval.pdf", file.read(), "application/pdf")},
            headers=headers,
        )
    document_id = upload.json()["id"]
    if upload.json().get("status") != "ready":
        raise RuntimeError(f"Eval document failed to process: {upload.json()}")

    result = run_eval(client, headers, document_id)
    _print_report(result)


if __name__ == "__main__":
    main()
