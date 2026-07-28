from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from skills.drive_web_helpers import (
    click_download_menu_item,
    click_export_format,
    file_row_locators,
    infer_workspace_kind,
    open_file_menu_download,
    pick_first_visible,
    preferred_export_formats,
)


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

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)

            file_row = pick_first_visible(file_row_locators(page, query))
            if file_row is None:
                context.close()
                return {
                    "action": "google_drive_web_download",
                    "status": "failed",
                    "error": f"No search result found for '{query}'.",
                    "download_dir": download_dir,
                }

            downloaded_path: str | None = None
            download_error: str | None = None
            method: str | None = None
            row_text = ""
            try:
                row_text = file_row.inner_text()
            except Exception:
                row_text = query
            kind = infer_workspace_kind(query, row_text)
            formats = preferred_export_formats(kind, query)

            def _save_download(dl_info: Any) -> str:
                download = dl_info.value
                target = Path(download_dir) / download.suggested_filename
                download.save_as(str(target))
                return str(target)

            # Strategy 1: right-click context menu -> Download
            try:
                file_row.click(button="right")
                page.wait_for_timeout(500)
                with page.expect_download(timeout=45000) as dl_info:
                    if not click_download_menu_item(page):
                        raise RuntimeError("Download menu item not found in context menu")
                downloaded_path = _save_download(dl_info)
                method = "context_download"
            except Exception as exc:
                download_error = str(exc)

            # Strategy 2: select row -> More actions (three-dot) -> Download
            if downloaded_path is None:
                try:
                    file_row.click()
                    page.wait_for_timeout(400)
                    more_btn = page.locator('[aria-label="More actions"], [data-tooltip="More actions"]').first
                    if more_btn.count() == 0:
                        raise RuntimeError("More actions button not found")
                    more_btn.click()
                    page.wait_for_timeout(400)
                    with page.expect_download(timeout=45000) as dl_info:
                        if not click_download_menu_item(page):
                            raise RuntimeError("Download menu item not found in overflow menu")
                    downloaded_path = _save_download(dl_info)
                    method = "overflow_download"
                except Exception as exc:
                    download_error = f"{download_error}; overflow: {exc}" if download_error else str(exc)

            # Strategy 3: keyboard context menu -> Download
            if downloaded_path is None:
                try:
                    file_row.click()
                    page.keyboard.press("Shift+F10")
                    page.wait_for_timeout(400)
                    with page.expect_download(timeout=45000) as dl_info:
                        if not click_download_menu_item(page):
                            raise RuntimeError("Download menu item not found via keyboard menu")
                    downloaded_path = _save_download(dl_info)
                    method = "keyboard_download"
                except Exception as exc:
                    download_error = f"{download_error}; keyboard: {exc}" if download_error else str(exc)

            # Strategy 4: native Workspace export submenu (Docs/Sheets/Slides)
            # Drive: right-click -> Download -> PDF / DOCX / XLSX / CSV
            if downloaded_path is None:
                try:
                    file_row.click(button="right")
                    page.wait_for_timeout(500)
                    with page.expect_download(timeout=60000) as dl_info:
                        if not click_export_format(page, formats):
                            raise RuntimeError(f"Export format not found for {formats}")
                    downloaded_path = _save_download(dl_info)
                    method = f"context_export:{kind or 'unknown'}"
                except Exception as exc:
                    download_error = f"{download_error}; export: {exc}" if download_error else str(exc)

            # Strategy 5: open editor -> File -> Download -> format
            if downloaded_path is None:
                try:
                    with context.expect_page(timeout=15000) as new_page_info:
                        file_row.dblclick()
                    editor = new_page_info.value
                    editor.wait_for_load_state("domcontentloaded")
                    editor.wait_for_timeout(2000)
                    with editor.expect_download(timeout=60000) as dl_info:
                        if not open_file_menu_download(editor, formats):
                            raise RuntimeError("File > Download export failed in editor")
                    downloaded_path = _save_download(dl_info)
                    method = f"editor_export:{kind or 'unknown'}"
                    try:
                        editor.close()
                    except Exception:
                        pass
                except Exception as exc:
                    # Some Drive views open in same tab
                    try:
                        file_row.dblclick()
                        page.wait_for_timeout(2500)
                        with page.expect_download(timeout=60000) as dl_info:
                            if not open_file_menu_download(page, formats):
                                raise RuntimeError("File > Download export failed in same tab")
                        downloaded_path = _save_download(dl_info)
                        method = f"same_tab_export:{kind or 'unknown'}"
                    except Exception as exc2:
                        download_error = (
                            f"{download_error}; editor_export: {exc}; same_tab: {exc2}"
                            if download_error
                            else f"{exc}; {exc2}"
                        )

            context.close()

            if downloaded_path:
                return {
                    "action": "google_drive_web_download",
                    "status": "executed",
                    "query": query,
                    "path": downloaded_path,
                    "method": method,
                    "workspace_kind": kind,
                    "download_dir": download_dir,
                }

            return {
                "action": "google_drive_web_download",
                "status": "failed",
                "error": download_error or "Download/export could not be triggered.",
                "query": query,
                "workspace_kind": kind,
                "tried_formats": formats,
                "download_dir": download_dir,
                "hint": "For Google Docs/Sheets, prefer export formats or use Drive API with OAuth.",
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
            page.goto("https://drive.google.com", wait_until="domcontentloaded")
            if headless:
                context.close()
                return {
                    "action": "bootstrap_google_login",
                    "status": "planned",
                    "note": "Headless mode cannot complete interactive login. Re-run with headless=False on desktop.",
                }
            # Interactive: wait until user completes login (Drive home loads).
            for _ in range(120):
                page.wait_for_timeout(5000)
                title = page.title().lower()
                url = page.url.lower()
                if "drive.google.com" in url and "sign" not in title and "accounts.google" not in url:
                    context.close()
                    return {
                        "action": "bootstrap_google_login",
                        "status": "executed",
                        "note": "Google Drive login detected. Persistent profile saved.",
                        "profile_dir": user_data_dir,
                    }
            context.close()
            return {
                "action": "bootstrap_google_login",
                "status": "failed",
                "error": "Timed out waiting for Google Drive login.",
            }
    except Exception as exc:
        return {"action": "bootstrap_google_login", "status": "failed", "error": str(exc)}
