from skills.vision_agent import VisionGuidedAgent
from connector.mobile.appium_stub import AppiumConnector


def test_vision_agent_completes_without_ollama() -> None:
    agent = VisionGuidedAgent()
    res = agent.run("type hello in notepad", app="notepad", max_loops=1)
    assert res["action"] == "vision_guided"
    assert res["status"] in {"completed", "max_loops"}
    assert len(res["loops"]) >= 1


def test_appium_stub_is_honest() -> None:
    stub = AppiumConnector()
    res = stub.run_intent("open maps on android")
    assert res["status"] == "unsupported"
    assert stub.status()["status"] == "stub"
