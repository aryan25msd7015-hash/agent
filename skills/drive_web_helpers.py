from __future__ import annotations

import re
from typing import Any


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def file_row_locators(page: Any, query: str) -> list[Any]:
    """Return ordered locators that may match a Drive search result row."""
    q = query.strip()
    locators = [
        page.get_by_role("option", name=re.compile(re.escape(q), re.I)),
        page.get_by_role("gridcell", name=re.compile(re.escape(q), re.I)),
        page.locator('[data-target="doc"]').filter(has_text=re.compile(re.escape(q), re.I)),
        page.locator('[role="row"]').filter(has_text=re.compile(re.escape(q), re.I)),
        page.get_by_text(q, exact=False),
    ]
    return locators


def pick_first_visible(locators: list[Any]) -> Any | None:
    for loc in locators:
        try:
            if loc.count() > 0:
                first = loc.first
                if first.is_visible():
                    return first
        except Exception:
            continue
    return None


def click_download_menu_item(page: Any) -> bool:
    """Try common Download menu labels in context/overflow menus."""
    labels = [
        re.compile(r"^Download$", re.I),
        re.compile(r"Download", re.I),
        re.compile(r"^Export$", re.I),
    ]
    for label in labels:
        item = page.get_by_role("menuitem", name=label)
        if item.count() > 0:
            item.first.click()
            return True
        item = page.get_by_text(label)
        if item.count() > 0:
            item.first.click()
            return True
    return False
