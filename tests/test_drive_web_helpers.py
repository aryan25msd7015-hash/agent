from skills.drive_web_helpers import (
    infer_workspace_kind,
    normalize_query,
    pick_first_visible,
    preferred_export_formats,
)


class _FakeLocator:
    def __init__(self, count: int, visible: bool = True) -> None:
        self._count = count
        self._visible = visible

    def count(self) -> int:
        return self._count

    @property
    def first(self) -> "_FakeLocator":
        return self

    def is_visible(self) -> bool:
        return self._visible


def test_normalize_query() -> None:
    assert normalize_query("  Quarterly   Report  ") == "quarterly report"


def test_pick_first_visible() -> None:
    locs = [_FakeLocator(0), _FakeLocator(2, True), _FakeLocator(1)]
    picked = pick_first_visible(locs)
    assert picked is not None
    assert picked.count() == 2


def test_infer_workspace_kind() -> None:
    assert infer_workspace_kind("budget sheet", "Google Sheets") == "sheets"
    assert infer_workspace_kind("report.gdoc", "") == "docs"
    assert infer_workspace_kind("deck.gslides", "") == "slides"


def test_preferred_export_formats_sheets_csv() -> None:
    formats = preferred_export_formats("sheets", "sales.csv")
    assert "Comma Separated Values (.csv)" in formats[0]


def test_preferred_export_formats_docs_pdf() -> None:
    formats = preferred_export_formats("docs", "notes.pdf")
    assert "PDF Document (.pdf)" in formats[0]
