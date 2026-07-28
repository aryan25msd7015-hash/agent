from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PrefStore:
    def __init__(self, path: str = "brain/memory/prefs.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._read().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self._read()
        data[key] = value
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def all(self) -> dict[str, Any]:
        return self._read()

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
