from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from threading import Lock
from typing import Any
from uuid import uuid4


class JsonStore:
    def __init__(self, path: str = "data/studywise.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        self.lock = Lock()
        if not self.path.exists():
            with self.lock, self._file_lock():
                if not self.path.exists():
                    self._write(self._empty())

    def _empty(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "users": [],
            "documents": [],
            "document_chunks": [],
            "chunk_propositions": [],
            "rag_traces": [],
            "chat_messages": [],
            "quizzes": [],
            "quiz_questions": [],
            "quiz_attempts": [],
            "quiz_answers": [],
            "weak_topics": [],
            "flashcards": [],
            "evaluation_metrics": [],
        }

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        last_error: Exception | None = None
        for _ in range(3):
            try:
                with self.path.open("r", encoding="utf-8-sig") as file:
                    return json.load(file)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(0.05)
        raise RuntimeError("Local data store could not be read. Please retry the request.") from last_error

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        temp_path = self.path.with_name(f".{self.path.name}.{os.getpid()}.{time.time_ns()}.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        try:
            self._replace_with_retry(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def _replace_with_retry(self, temp_path: Path) -> None:
        last_error: PermissionError | None = None
        for attempt in range(8):
            try:
                os.replace(temp_path, self.path)
                return
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.05 * (attempt + 1))
        raise RuntimeError("Local data store is busy. Please retry the request.") from last_error

    @contextmanager
    def _file_lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as lock_file:
            try:
                if os.name == "nt":
                    import msvcrt

                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                yield
            finally:
                if os.name == "nt":
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)

    def all(self, table: str) -> list[dict[str, Any]]:
        with self.lock, self._file_lock():
            return deepcopy(self._read().get(table, []))

    def find(self, table: str, **filters: Any) -> dict[str, Any] | None:
        for row in self.all(table):
            if all(row.get(key) == value for key, value in filters.items()):
                return row
        return None

    def filter(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        return [
            row
            for row in self.all(table)
            if all(row.get(key) == value for key, value in filters.items())
        ]

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        stored = {"id": str(uuid4()), "created_at": now, **row}
        stored.setdefault("updated_at", now)
        with self.lock, self._file_lock():
            data = self._read()
            data.setdefault(table, []).append(stored)
            self._write(data)
        return deepcopy(stored)

    def update(self, table: str, row_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self.lock, self._file_lock():
            data = self._read()
            for index, row in enumerate(data.get(table, [])):
                if row.get("id") == row_id:
                    data[table][index] = {
                        **row,
                        **updates,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    self._write(data)
                    return deepcopy(data[table][index])
        return None

    def delete(self, table: str, row_id: str) -> bool:
        with self.lock, self._file_lock():
            data = self._read()
            original_count = len(data.get(table, []))
            data[table] = [row for row in data.get(table, []) if row.get("id") != row_id]
            self._write(data)
            return len(data[table]) < original_count


store = JsonStore()
