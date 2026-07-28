from brain.graph import build_router
from skills.onedrive import download_onedrive_file
from skills.dropbox_skill import download_dropbox_file


def test_onedrive_dropbox_routes() -> None:
    router = build_router()
    assert router.invoke({"intent": "download report.csv from onedrive", "route": ""})["route"] == "onedrive"
    assert router.invoke({"intent": "download report.csv from dropbox", "route": ""})["route"] == "dropbox"


def test_onedrive_dropbox_require_tokens() -> None:
    od = download_onedrive_file("x.csv", "data/inbox")
    db = download_dropbox_file("x.csv", "data/inbox")
    assert od["status"] == "failed"
    assert db["status"] == "failed"
