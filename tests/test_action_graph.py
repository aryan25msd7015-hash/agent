from skills.action_graph import parse_action_graph


def test_parse_action_graph() -> None:
    app, steps = parse_action_graph("automate chrome: hotkey ctrl+l; type github.com; press enter")
    assert app == "chrome"
    assert len(steps) == 3
    assert steps[0].action == "hotkey"
    assert steps[1].action == "type"
    assert steps[2].action == "press"
