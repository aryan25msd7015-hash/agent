from __future__ import annotations

import os
from pathlib import Path


def open_path(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    os.startfile(str(p))  # type: ignore[attr-defined]
    return f"Opened {p}"


def list_dir(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    items = sorted(x.name for x in p.iterdir())
    return "\n".join(items[:200]) or "(empty)"
