from skills.download_gdrive import _choose_export


def test_choose_export_sheets_csv() -> None:
    mime, ext = _choose_export("application/vnd.google-apps.spreadsheet", "sales.csv")
    assert ext == ".csv"
    assert mime == "text/csv"


def test_choose_export_docs_pdf_default() -> None:
    mime, ext = _choose_export("application/vnd.google-apps.document", "notes")
    assert ext == ".pdf"


def test_choose_export_binary_returns_none() -> None:
    assert _choose_export("text/csv", "sales.csv") is None
