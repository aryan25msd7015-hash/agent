from brain.planner import heuristic_plan, plan_action_graph


def test_heuristic_plans_notepad_type() -> None:
    cmd = heuristic_plan("open notepad and type hello world")
    assert cmd == "automate notepad: type hello world"


def test_heuristic_plans_chrome_navigation() -> None:
    cmd = heuristic_plan("in chrome go to github.com")
    assert cmd is not None
    assert cmd.startswith("automate chrome:")
    assert "github.com" in cmd


def test_heuristic_skips_mobile_intents() -> None:
    assert heuristic_plan("open notepad on my android tablet") is None


def test_plan_action_graph_falls_back_offline() -> None:
    # Ollama likely offline in CI; heuristic should still work.
    cmd = plan_action_graph("open notepad and type hi")
    assert cmd == "automate notepad: type hi"
