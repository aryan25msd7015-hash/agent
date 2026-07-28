from __future__ import annotations

import os
from pathlib import Path


def allowed_roots() -> list[Path]:
    raw = os.getenv(
        "ALLOWED_PATH_ROOTS",
        ".,data,artifacts,brain/memory,logs,D:/Agent,D:/Dashboards,C:/Users",
    )
    roots = []
    for part in raw.split(","):
        p = part.strip()
        if p:
            roots.append(Path(p).expanduser())
    return roots


def is_path_allowed(path: str) -> bool:
    target = Path(path).expanduser().resolve()
    for root in allowed_roots():
        try:
            resolved = root.resolve()
            if target == resolved or resolved in target.parents or str(target).startswith(str(resolved)):
                return True
        except Exception:
            # root may not exist yet
            if str(target).lower().startswith(str(root).lower()):
                return True
    return False


def assert_path_allowed(path: str) -> None:
    if not is_path_allowed(path):
        raise PermissionError(f"Path not allowed by policy: {path}")
