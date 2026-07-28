from __future__ import annotations

import re
from skills.ui_automation import ActionStep


def parse_action_graph(intent: str) -> tuple[str, list[ActionStep]]:
    """
    Very small grammar:
    "automate <app>: <cmd>; <cmd>; ..."
    cmd supports:
      - hotkey ctrl+l
      - type hello
      - press enter
      - wait 1
    """
    match = re.match(r"^\s*automate\s+([^:]+)\s*:\s*(.+)$", intent, flags=re.IGNORECASE)
    if not match:
        return ("", [])
    app = match.group(1).strip()
    cmds = [c.strip() for c in match.group(2).split(";") if c.strip()]
    steps: list[ActionStep] = []
    for cmd in cmds:
        lower = cmd.lower()
        if lower.startswith("hotkey "):
            steps.append(ActionStep(action="hotkey", value=cmd[7:].strip()))
        elif lower.startswith("type "):
            steps.append(ActionStep(action="type", value=cmd[5:]))
        elif lower.startswith("press "):
            steps.append(ActionStep(action="press", value=cmd[6:].strip()))
        elif lower.startswith("wait "):
            steps.append(ActionStep(action="wait", value=cmd[5:].strip()))
    return app, steps
