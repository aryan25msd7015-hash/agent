from skills.window_manager import WindowManager
from skills.screenshot import capture_screenshot, verify_screenshot_exists
from skills.ui_automation import ActionStep, UIAutomationEngine


def test_window_manager_dry_run_on_linux() -> None:
    wm = WindowManager()
    res = wm.focus("notepad")
    assert "focused" in res


def test_screenshot_pipeline(tmp_path) -> None:
    out = tmp_path / "shot.png"
    cap = capture_screenshot(str(out))
    assert cap["status"] in {"captured", "placeholder"}
    assert verify_screenshot_exists(str(out))


def test_ui_engine_includes_focus_and_verify() -> None:
    engine = UIAutomationEngine()
    res = engine.execute("notepad", [ActionStep(action="type", value="hi"), ActionStep(action="wait", value="0.01")])
    assert res["steps_executed"] == 2
    assert "focus" in res
    assert isinstance(res["logs"], list)
