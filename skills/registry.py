from __future__ import annotations

import os
from pathlib import Path

from config.allowlist import assert_path_allowed


def open_path(path: str) -> str:
    assert_path_allowed(path)
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    os.startfile(str(p))  # type: ignore[attr-defined]
    return f"Opened {p}"


def list_dir(path: str) -> str:
    assert_path_allowed(path)
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    items = sorted(x.name for x in p.iterdir())
    return "\n".join(items[:200]) or "(empty)"
