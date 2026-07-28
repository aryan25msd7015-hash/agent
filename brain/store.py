from __future__ import annotations

import json
import os
import sqlite3
import uuid
from typing import Any

from brain.models import Task


class TaskStore:
    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                intent TEXT NOT NULL,
                status TEXT NOT NULL,
                target_device TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                result TEXT,
                metadata TEXT
            )
            """
        )
        self._conn.commit()

    def create_task(self, intent: str, target_device: str, metadata: dict[str, Any] | None = None) -> Task:
        task_id = str(uuid.uuid4())
        now = Task.now_iso()
        self._conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, intent, "pending", target_device, now, now, None, json.dumps(metadata or {})),
        )
        self._conn.commit()
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> Task:
        row = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return Task(
            id=row["id"],
            intent=row["intent"],
            status=row["status"],
            target_device=row["target_device"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            result=row["result"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_pending(self, target_device: str) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE status = 'pending' AND target_device = ? ORDER BY created_at ASC",
            (target_device,),
        ).fetchall()
        return [self.get_task(r["id"]) for r in rows]

    def update_task(self, task_id: str, *, status: str | None = None, result: str | None = None) -> Task:
        task = self.get_task(task_id)
        next_status = status or task.status
        next_result = task.result if result is None else result
        self._conn.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (next_status, next_result, Task.now_iso(), task_id),
        )
        self._conn.commit()
        return self.get_task(task_id)

    def update_metadata(self, task_id: str, metadata: dict[str, Any]) -> Task:
        task = self.get_task(task_id)
        next_meta = dict(task.metadata or {})
        next_meta.update(metadata)
        self._conn.execute(
            "UPDATE tasks SET metadata = ?, updated_at = ? WHERE id = ?",
            (json.dumps(next_meta), Task.now_iso(), task_id),
        )
        self._conn.commit()
        return self.get_task(task_id)
