"""AI evaluation test (PRD 19: AI Evaluation Tests).

Runs the fixed question set in tests/fixtures/rag_eval_set.json against a
synthetic multi-page document and checks the pipeline meets baseline
quality bars for retrieval, citations, groundedness, and refusal on
out-of-scope questions (retriever.py gates on the cross-encoder's top
relevance score; see RELEVANCE_THRESHOLD).
"""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from scripts.rag_eval import run_eval
from tests.fixtures.eval_document import write_eval_pdf


def test_rag_eval_meets_baseline_quality_bars(tmp_path) -> None:
    client = TestClient(app)
    suffix = uuid4().hex
    register = client.post(
        "/api/v1/auth/register",
        json={"name": f"Eval User {suffix}", "email": f"rag-eval-{suffix}@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    pdf_path = write_eval_pdf(tmp_path / "eval.pdf")
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("eval.pdf", pdf_path.read_bytes(), "application/pdf")},
        headers=headers,
    )
    document_id = upload.json()["id"]
    assert upload.json()["status"] == "ready"

    result = run_eval(client, headers, document_id)
    metrics = result["metrics"]
    print(metrics)

    assert metrics["retrieval_accuracy"] >= 0.8
    assert metrics["citation_coverage"] >= 0.8
    assert metrics["answer_groundedness"] >= 0.6
    assert metrics["refusal_accuracy"] >= 0.8
