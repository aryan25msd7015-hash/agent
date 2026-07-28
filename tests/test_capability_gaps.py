"""Document current capability limits (expected behaviors, not bugs in tests)."""

from brain.graph import build_router
from brain.orchestrator import Orchestrator
from skills.browser_automation import run_workflow


def test_natural_language_google_drive_download_routes_to_gdrive() -> None:
    router = build_router()
    state = router.invoke({"intent": "navigate google drive and download quarterly_report.csv", "route": ""})
    assert state["route"] == "gdrive"


def test_google_drive_web_hits_signin_without_session() -> None:
    result = run_workflow("https://drive.google.com", actions=[], headless=True)
    if result.get("status") == "executed":
        assert "sign" in (result.get("title") or "").lower()
    else:
        assert result.get("status") == "planned"


def test_mobile_device_intent_does_not_execute_on_device() -> None:
    orch = Orchestrator()
    result = orch.run("open notepad on my android tablet")
    assert result["action"] == "open_path"
    assert result.get("status") == "failed"


def test_desktop_app_requires_automate_prefix() -> None:
    router = build_router()
    state = router.invoke({"intent": "open excel and create a pivot table", "route": ""})
    assert state["route"] == "chat"
