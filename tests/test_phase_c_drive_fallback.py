from unittest.mock import patch

from brain.orchestrator import Orchestrator


@patch("brain.orchestrator.google_drive_web_download")
@patch("brain.orchestrator.download_file_by_name", side_effect=FileNotFoundError("missing oauth"))
@patch("brain.orchestrator.search_files", side_effect=FileNotFoundError("missing oauth"))
def test_drive_api_falls_back_to_web(mock_search, mock_download, mock_web) -> None:
    mock_web.return_value = {
        "action": "google_drive_web_download",
        "status": "executed",
        "path": "data/inbox/sales.csv",
        "method": "context_download",
    }
    orch = Orchestrator()
    res = orch.run("download sales.csv from google drive")
    assert res.get("fallback") == "web" or res.get("action") == "google_drive_web_download"
    assert res.get("status") == "executed"
