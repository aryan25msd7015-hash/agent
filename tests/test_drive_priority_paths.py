from unittest.mock import patch

from brain.orchestrator import Orchestrator


@patch("brain.orchestrator.search_files")
@patch("brain.orchestrator.download_file_by_name")
def test_priority1_drive_api_hardened(mock_download, mock_search) -> None:
    mock_search.return_value = [{"name": "quarterly_report.csv"}]
    mock_download.return_value = "data/inbox/quarterly_report.csv"
    orch = Orchestrator()
    res = orch.run("download quarterly report from google drive")
    assert res["action"] == "download_gdrive"
    assert res["path"].endswith(".csv")
    assert isinstance(res["candidates"], list)


@patch("brain.orchestrator.google_drive_web_download")
def test_priority2_drive_web_route(mock_drive_web) -> None:
    mock_drive_web.return_value = {"action": "google_drive_web_download", "status": "executed"}
    orch = Orchestrator()
    res = orch.run("browse https://drive.google.com download quarterly_report.csv")
    assert res["action"] == "google_drive_web_download"
