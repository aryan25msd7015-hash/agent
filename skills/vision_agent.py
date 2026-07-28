from __future__ import annotations

import json
from typing import Any

import httpx

from config.settings import settings
from skills.screenshot import capture_screenshot
from skills.ui_automation import ActionStep, UIAutomationEngine


VISION_PROMPT = """You are a desktop UI verifier.
Given a user goal and a list of executed steps, propose the NEXT single automate command if the goal is incomplete.
Return ONLY one line:
automate <app>: <step>; <step>
or DONE if goal appears complete.
Goal: {goal}
Steps so far: {steps}
"""


class VisionGuidedAgent:
    def __init__(self) -> None:
        self.ui = UIAutomationEngine()

    def run(self, goal: str, app: str = "desktop", max_loops: int = 3) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        command = f"automate {app}: wait 1"
        for i in range(max_loops):
            from skills.action_graph import parse_action_graph

            parsed_app, steps = parse_action_graph(command)
            if not steps:
                steps = [ActionStep(action="wait", value="1")]
                parsed_app = app
            execution = self.ui.execute(parsed_app or app, steps, verify=True)
            shot = capture_screenshot(f"artifacts/screenshots/vision_{i + 1}.png")
            nxt = self._next_command(goal, execution.get("logs", []))
            history.append({"loop": i + 1, "command": command, "execution": execution, "screenshot": shot, "next": nxt})
            if not nxt or nxt.strip().upper() == "DONE":
                return {"action": "vision_guided", "status": "completed", "loops": history}
            command = nxt
        return {"action": "vision_guided", "status": "max_loops", "loops": history}

    def _next_command(self, goal: str, steps: list[str]) -> str:
        payload = {
            "model": settings.ollama_model,
            "prompt": VISION_PROMPT.format(goal=goal, steps=json.dumps(steps)),
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            res = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=45)
            res.raise_for_status()
            text = (res.json().get("response") or "").strip()
            for line in text.splitlines():
                line = line.strip()
                if line.upper() == "DONE":
                    return "DONE"
                if line.lower().startswith("automate "):
                    return line
        except Exception:
            pass
        return "DONE"
