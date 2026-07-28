from brain.orchestrator import Orchestrator


def test_nl_desktop_intent_becomes_ui_automation() -> None:
    orch = Orchestrator()
    res = orch.run("open notepad and type hello")
    assert res["action"] == "ui_automation"
    assert "automate notepad" in res["command"]
    assert res["execution"]["steps_executed"] >= 1
