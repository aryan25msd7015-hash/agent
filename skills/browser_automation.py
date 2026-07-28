from __future__ import annotations

from pathlib import Path
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
    """Open a URL in a headless browser when Playwright is available."""
    return run_workflow(url, actions=[], headless=True)


def google_drive_web_download(
    query: str,
    download_dir: str,
    user_data_dir: str,
    headless: bool = True,
) -> dict[str, Any]:
    """
    Best-effort Google Drive web automation using a persistent browser profile.
    Requires the profile to already be logged into Google Drive.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {
            "action": "google_drive_web_download",
            "status": "planned",
            "error": "Playwright not available.",
        }

    Path(download_dir).mkdir(parents=True, exist_ok=True)
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                accept_downloads=True,
                downloads_path=download_dir,
            )
            page = context.new_page()
            page.goto("https://drive.google.com", wait_until="domcontentloaded")
            title = page.title()
            if "sign-in" in title.lower() or "signin" in title.lower():
                context.close()
                return {
                    "action": "google_drive_web_download",
                    "status": "failed",
                    "error": "Google Drive session not logged in. Run login bootstrap first.",
                    "title": title,
                }

            search_selectors = [
                'input[aria-label*="Search in Drive"]',
                'input[placeholder*="Search in Drive"]',
                'input[role="combobox"]',
            ]
            found = False
            for sel in search_selectors:
                if page.locator(sel).count() > 0:
                    page.fill(sel, query)
                    page.press(sel, "Enter")
                    found = True
                    break
            if not found:
                context.close()
                return {
                    "action": "google_drive_web_download",
                    "status": "failed",
                    "error": "Could not find Drive search box selector.",
                }

            page.wait_for_timeout(3000)
            context.close()
            return {
                "action": "google_drive_web_download",
                "status": "executed",
                "query": query,
                "note": "Search executed on Drive web UI. Download click flow is site-layout dependent.",
                "download_dir": download_dir,
            }
    except Exception as exc:
        return {
            "action": "google_drive_web_download",
            "status": "failed",
            "error": str(exc),
        }


def bootstrap_google_login(user_data_dir: str, headless: bool = False) -> dict[str, Any]:
    """
    One-time helper: opens Chromium persistent profile so user can log into Google manually.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {"action": "bootstrap_google_login", "status": "failed", "error": "Playwright not available."}

    Path(user_data_dir).mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, headless=headless)
            page = context.new_page()
            page.goto("https://accounts.google.com", wait_until="domcontentloaded")
            if headless:
                context.close()
                return {
                    "action": "bootstrap_google_login",
                    "status": "planned",
                    "note": "Headless mode cannot complete interactive login. Re-run with headless=False on desktop.",
                }
            return {
                "action": "bootstrap_google_login",
                "status": "interactive",
                "note": "Complete login in opened browser, then close browser window.",
            }
    except Exception as exc:
        return {"action": "bootstrap_google_login", "status": "failed", "error": str(exc)}
