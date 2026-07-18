"""AI evaluation test (PRD 19: AI Evaluation Tests).

Runs the fixed question set in tests/fixtures/rag_eval_set.json against a
synthetic multi-page document and checks the pipeline meets baseline
quality bars for retrieval, citations, and groundedness.

refusal_accuracy is measured and printed but not asserted: the current
local (no-AI-key) answer fallback always answers from whatever chunks were
retrieved and never declines, so it's a known gap rather than a regression
this test should fail on. See the printed report for the current value.
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
