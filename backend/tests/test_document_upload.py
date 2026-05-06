from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_oversized_upload_returns_413_without_file_lock_error(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(
        "app.api.v1.documents.get_settings",
        lambda: type("Settings", (), {"max_upload_size_mb": 0, "upload_path": Path("uploads")})(),
    )
    suffix = uuid4().hex
    response = client.post(
        "/api/v1/auth/register",
        json={"name": f"Upload Limit User {suffix}", "email": f"upload-limit-{suffix}@example.com", "password": "Password123!"},
    )
    token = response.json()["access_token"]

    upload = client.post(
        "/api/v1/documents",
        files={"file": ("large.pdf", b"%PDF-content", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert upload.status_code == 413
    assert upload.json()["detail"] == "File is too large for the MVP upload limit."
