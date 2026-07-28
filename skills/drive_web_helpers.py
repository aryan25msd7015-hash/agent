from __future__ import annotations

import re
from typing import Any


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def infer_workspace_kind(query: str, row_text: str = "") -> str | None:
    """
    Infer Google Workspace type from query/row text.
    Returns: docs | sheets | slides | None
    """
    hay = f"{query} {row_text}".lower()
    if any(x in hay for x in [".gsheet", "spreadsheet", "sheet", "xlsx", "csv"]):
        return "sheets"
    if any(x in hay for x in [".gdoc", "document", "docs", "docx", "pdf"]):
        return "docs"
    if any(x in hay for x in [".gslides", "presentation", "slides", "pptx"]):
        return "slides"
    return None


def preferred_export_formats(kind: str | None, query: str) -> list[str]:
    """Ordered export format labels to try in Google Drive/Docs menus."""
    q = query.lower()
    if kind == "sheets":
        if ".csv" in q:
            return ["Comma Separated Values (.csv)", "Microsoft Excel (.xlsx)", "PDF Document (.pdf)"]
        return ["Microsoft Excel (.xlsx)", "Comma Separated Values (.csv)", "PDF Document (.pdf)"]
    if kind == "slides":
        return ["Microsoft PowerPoint (.pptx)", "PDF Document (.pdf)"]
    # docs default
    if ".docx" in q:
        return ["Microsoft Word (.docx)", "PDF Document (.pdf)"]
    if ".pdf" in q:
        return ["PDF Document (.pdf)", "Microsoft Word (.docx)"]
    return ["PDF Document (.pdf)", "Microsoft Word (.docx)", "Plain Text (.txt)"]


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


def click_menu_label(page: Any, labels: list[re.Pattern[str] | str]) -> bool:
    for label in labels:
        pattern = re.compile(label, re.I) if isinstance(label, str) else label
        item = page.get_by_role("menuitem", name=pattern)
        if item.count() > 0:
            item.first.click()
            return True
        item = page.get_by_text(pattern)
        if item.count() > 0:
            item.first.click()
            return True
    return False


def click_download_menu_item(page: Any) -> bool:
    """Try common Download menu labels in context/overflow menus."""
    return click_menu_label(
        page,
        [
            re.compile(r"^Download$", re.I),
            re.compile(r"Download", re.I),
        ],
    )


def click_export_format(page: Any, format_labels: list[str]) -> bool:
    """
    Open Download/Export submenu and choose a concrete format.
    Drive often shows: Download > Microsoft Word (.docx) / PDF ...
    """
    # Ensure Download/Export submenu is open
    opened = click_menu_label(
        page,
        [
            re.compile(r"^Download$", re.I),
            re.compile(r"^Export$", re.I),
            re.compile(r"Download", re.I),
            re.compile(r"Export", re.I),
        ],
    )
    if not opened:
        return False
    for label in format_labels:
        if click_menu_label(page, [re.compile(re.escape(label), re.I), label]):
            return True
        # Partial match e.g. ".pdf" / ".xlsx"
        short = label.split("(")[-1].strip(") ").lower() if "(" in label else label.lower()
        if short and click_menu_label(page, [re.compile(re.escape(short), re.I)]):
            return True
    return False


def open_file_menu_download(page: Any, format_labels: list[str]) -> bool:
    """Inside Docs/Sheets editor: File -> Download -> <format>."""
    if not click_menu_label(page, [re.compile(r"^File$", re.I), "File"]):
        # Docs often uses menubar role
        file_btn = page.locator('#docs-file-menu, [aria-label="File"]').first
        if file_btn.count() == 0:
            return False
        file_btn.click()
    return click_export_format(page, format_labels)
