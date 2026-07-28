from brain.orchestrator import Orchestrator


def test_orchestrator_ui_automation_route() -> None:
    orch = Orchestrator()
    res = orch.run("automate notepad: type hello; press enter")
    assert res["action"] == "ui_automation"
    assert res["execution"]["steps_executed"] == 2


def test_orchestrator_browser_route() -> None:
    orch = Orchestrator()
    res = orch.run("browse https://example.com")
    assert res["action"] == "browser_open_url"
