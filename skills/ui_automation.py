from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skills.screenshot import capture_screenshot, verify_screenshot_exists
from skills.window_manager import WindowManager


@dataclass
class ActionStep:
    action: str
    value: str | None = None
    x: int | None = None
    y: int | None = None


class UIAutomationEngine:
    """
    Generic UI action graph executor with:
    - window focus (pywinauto)
    - pyautogui actions
    - screenshot verify/retry after each step
    """

    def __init__(self) -> None:
        try:
            import pyautogui  # type: ignore

            self._pyautogui = pyautogui
        except BaseException:
            self._pyautogui = None
        self.windows = WindowManager()

    def execute(
        self,
        app: str,
        steps: list[ActionStep],
        dry_run: bool = False,
        verify: bool = True,
        max_retries: int = 1,
        screenshot_dir: str = "artifacts/screenshots",
    ) -> dict[str, Any]:
        focus = self.windows.focus(app)
        results: list[str] = []
        screenshots: list[str] = []
        dry = dry_run or self._pyautogui is None

        for idx, step in enumerate(steps):
            attempts = 0
            while True:
                attempts += 1
                if dry:
                    results.append(f"dry-run: {step.action} {step.value or ''}".strip())
                    break
                try:
                    self._run_step(step)
                    results.append(f"executed: {step.action}")
                except Exception as exc:
                    results.append(f"error: {step.action}: {exc}")
                    if attempts <= max_retries:
                        continue
                    break

                if not verify:
                    break
                shot = Path(screenshot_dir) / f"step_{idx + 1}_try_{attempts}.png"
                cap = capture_screenshot(str(shot))
                if cap.get("path"):
                    screenshots.append(str(cap["path"]))
                if verify_screenshot_exists(str(shot)):
                    results.append(f"verified: screenshot {shot.name}")
                    break
                if attempts <= max_retries:
                    results.append(f"retry: verification failed for {step.action}")
                    continue
                results.append(f"unverified: {step.action}")
                break

        return {
            "app": app,
            "focus": focus,
            "dry_run": dry,
            "steps_executed": len(steps),
            "logs": results,
            "screenshots": screenshots,
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
            return
        if step.action == "focus" and step.value:
            self.windows.focus(step.value)
