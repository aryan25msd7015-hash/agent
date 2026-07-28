from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionStep:
    action: str
    value: str | None = None
    x: int | None = None
    y: int | None = None


class UIAutomationEngine:
    """
    Generic UI action graph executor.
    Uses pyautogui when available; otherwise returns dry-run execution.
    """

    def __init__(self) -> None:
        try:
            import pyautogui  # type: ignore

            self._pyautogui = pyautogui
        except BaseException:
            self._pyautogui = None

    def execute(self, app: str, steps: list[ActionStep], dry_run: bool = False) -> dict[str, Any]:
        results: list[str] = []
        for step in steps:
            if dry_run or self._pyautogui is None:
                results.append(f"dry-run: {step.action} {step.value or ''}".strip())
                continue
            self._run_step(step)
            results.append(f"executed: {step.action}")
        return {
            "app": app,
            "dry_run": dry_run or self._pyautogui is None,
            "steps_executed": len(steps),
            "logs": results,
        }

    def _run_step(self, step: ActionStep) -> None:
        pag = self._pyautogui
        if step.action == "hotkey" and step.value:
            keys = [k.strip() for k in step.value.split("+") if k.strip()]
            pag.hotkey(*keys)
            return
        if step.action == "type" and step.value:
            pag.write(step.value, interval=0.02)
            return
        if step.action == "press" and step.value:
            pag.press(step.value)
            return
        if step.action == "click" and step.x is not None and step.y is not None:
            pag.click(step.x, step.y)
            return
        if step.action == "wait" and step.value:
            import time

            time.sleep(float(step.value))
