from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Task:
    id: str
    intent: str
    status: str
    target_device: str
    created_at: str
    updated_at: str
    result: str | None = None
    metadata: dict[str, Any] | None = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
