from unittest.mock import patch

from brain.orchestrator import Orchestrator


@patch("brain.orchestrator.download_file_by_name")
@patch("brain.orchestrator.search_files")
def test_week1_download_flow(mock_search, mock_download) -> None:
    mock_search.return_value = [{"name": "sales_data.csv"}]
    mock_download.return_value = "data/inbox/sales_data.csv"
    orch = Orchestrator()
    res = orch.run("download sales_data.csv from gdrive")
    assert res["action"] == "download_gdrive"
    assert res["path"].endswith("sales_data.csv")


@patch("brain.orchestrator.build_twbx_from_template")
@patch("brain.orchestrator.download_file_by_name")
def test_week2_tableau_flow(mock_download, mock_build) -> None:
    mock_download.return_value = "data/inbox/sales_data.csv"
    mock_build.return_value = "artifacts/sales_data.twbx"
    orch = Orchestrator()
    res = orch.run("build tableau dashboard from sales_data.csv in gdrive")
    assert res["action"] == "build_tableau"
    assert res["twbx"].endswith(".twbx")
