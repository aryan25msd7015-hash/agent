from __future__ import annotations

from typing import Any


class WindowManager:
    """
    Attach/focus a desktop window by title/process hint.
    Uses pywinauto on Windows; dry-run elsewhere.
    """

    def __init__(self) -> None:
        try:
            from pywinauto import Desktop  # type: ignore

            self._desktop = Desktop(backend="uia")
            self._available = True
        except Exception:
            self._desktop = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def focus(self, app_hint: str) -> dict[str, Any]:
        hint = app_hint.strip()
        if not hint:
            return {"focused": False, "reason": "empty app hint"}
        if not self._available or self._desktop is None:
            return {"focused": False, "dry_run": True, "app": hint, "reason": "pywinauto unavailable"}
        try:
            windows = self._desktop.windows()
            matched = None
            for win in windows:
                try:
                    title = (win.window_text() or "").lower()
                    if hint.lower() in title:
                        matched = win
                        break
                except Exception:
                    continue
            if matched is None:
                # try launching via start menu search is out of scope; report miss
                return {"focused": False, "app": hint, "reason": "window not found"}
            matched.set_focus()
            return {"focused": True, "app": hint, "title": matched.window_text()}
        except Exception as exc:
            return {"focused": False, "app": hint, "error": str(exc)}
