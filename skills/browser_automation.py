from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def run_workflow(url: str, actions: list[dict[str, str]] | None = None, headless: bool = True) -> dict[str, Any]:
    """
    Execute a minimal Playwright workflow when available.
    Supported actions:
      - {"type":"click","selector":"..."}
      - {"type":"fill","selector":"...","value":"..."}
      - {"type":"press","selector":"...","value":"Enter"}
    """
    actions = actions or []
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {
            "action": "browser_workflow",
            "status": "planned",
            "url": url,
            "note": "Playwright not available at runtime; workflow returned as plan.",
            "actions": actions,
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            for action in actions:
                kind = action.get("type", "")
                selector = action.get("selector", "")
                value = action.get("value", "")
                if kind == "click" and selector:
                    page.click(selector)
                elif kind == "fill" and selector:
                    page.fill(selector, value)
                elif kind == "press" and selector:
                    page.press(selector, value or "Enter")
            title = page.title()
            browser.close()
            return {
                "action": "browser_workflow",
                "status": "executed",
                "url": url,
                "host": urlparse(url).netloc,
                "title": title,
                "actions_executed": len(actions),
            }
    except Exception as exc:
        return {
            "action": "browser_workflow",
            "status": "planned",
            "url": url,
            "note": f"Playwright runtime unavailable: {exc}",
            "actions": actions,
        }


def open_url(url: str) -> dict[str, Any]:
    """
    Browser automation hook.
    If Playwright is available, it can be extended to scripted flows.
    Current implementation returns an execution plan for safety.
    """
    return {
        "action": "browser_open_url",
        "url": url,
        "status": "planned",
        "note": "Hook ready. Add Playwright script execution per site workflow.",
    }
