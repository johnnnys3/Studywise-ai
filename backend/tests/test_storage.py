import json
import os
from pathlib import Path

from app.storage import JsonStore


def test_json_store_writes_valid_json_atomically() -> None:
    data_path = Path("data/test-storage.json")
    data_path.unlink(missing_ok=True)
    data_path.with_suffix(".json.lock").unlink(missing_ok=True)


def test_json_store_retries_locked_replace(monkeypatch) -> None:
    data_path = Path("data/test-storage-retry.json")
    data_path.unlink(missing_ok=True)
    data_path.with_suffix(".json.lock").unlink(missing_ok=True)
    original_replace = os.replace
    calls = {"count": 0}

    def flaky_replace(src, dst):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("locked")
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)
    store = JsonStore(str(data_path))
    store.insert("users", {"name": "Retry User", "email": "retry@example.com"})

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert calls["count"] >= 2
    assert data["users"][0]["name"] == "Retry User"

    data_path.unlink(missing_ok=True)
    data_path.with_suffix(".json.lock").unlink(missing_ok=True)
    store = JsonStore(str(data_path))

    user = store.insert("users", {"name": "Test User", "email": "test@example.com"})
    store.update("users", user["id"], {"name": "Updated User"})

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["users"][0]["name"] == "Updated User"
    assert not list(data_path.parent.glob(".test-storage.json.*.tmp"))

    data_path.unlink(missing_ok=True)
    data_path.with_suffix(".json.lock").unlink(missing_ok=True)
