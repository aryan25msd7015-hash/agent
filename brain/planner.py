from __future__ import annotations

import json
import re
from typing import Any

import httpx

from config.settings import settings


PLANNER_PROMPT = """You convert a user's desktop instruction into ONE automation command.
Return ONLY a single line in this exact format:
automate <app>: <step>; <step>; <step>

Allowed steps:
- hotkey <keys>   e.g. hotkey ctrl+l
- type <text>
- press <key>     e.g. press enter
- wait <seconds>

Examples:
User: open notepad and type hello world
automate notepad: type hello world

User: in chrome go to github.com
automate chrome: hotkey ctrl+l; type github.com; press enter

User: open excel
automate excel: wait 1

If you cannot convert confidently, reply exactly: UNPLANABLE
User: {intent}
"""


def plan_action_graph(intent: str) -> str | None:
    """Ask local Ollama to convert NL desktop intent into automate command."""
    payload = {
        "model": settings.ollama_model,
        "prompt": PLANNER_PROMPT.format(intent=intent),
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        res = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=45)
        res.raise_for_status()
        text = (res.json().get("response") or "").strip()
    except Exception:
        return heuristic_plan(intent)

    line = _extract_automate_line(text)
    if line:
        return line
    return heuristic_plan(intent)


def heuristic_plan(intent: str) -> str | None:
    """Offline fallback planner when Ollama is unavailable."""
    lower = intent.lower().strip()
    if any(x in lower for x in ("phone", "tablet", "android", "ios", "ipad")):
        return None
    # "open notepad and type hello"
    m = re.search(r"open\s+([a-zA-Z0-9_\- ]+?)(?:\s+and\s+type\s+(.+))?$", lower)
    if m:
        app = m.group(1).strip()
        if any(x in app for x in ("phone", "tablet", "android", "ios")):
            return None
        typed = (m.group(2) or "").strip()
        if typed:
            return f"automate {app}: type {typed}"
        # Require a known-ish short app name, not a long sentence.
        if len(app.split()) > 3:
            return None
        return f"automate {app}: wait 1"
    m = re.search(r"(?:in|on)\s+(chrome|edge|firefox).*?(?:go to|open)\s+(\S+)", lower)
    if m:
        app, url = m.group(1), m.group(2)
        return f"automate {app}: hotkey ctrl+l; type {url}; press enter"
    m = re.search(r"type\s+(.+)\s+in\s+([a-zA-Z0-9_\- ]+)$", lower)
    if m:
        text, app = m.group(1).strip(), m.group(2).strip()
        return f"automate {app}: type {text}"
    return None


def _extract_automate_line(text: str) -> str | None:
    for raw in text.splitlines():
        line = raw.strip().strip("`").strip()
        if line.lower().startswith("automate ") and ":" in line:
            return line
    if text.strip().upper() == "UNPLANABLE":
        return None
    # sometimes model returns JSON
    try:
        body: Any = json.loads(text)
        if isinstance(body, dict) and "command" in body:
            cmd = str(body["command"]).strip()
            if cmd.lower().startswith("automate "):
                return cmd
    except Exception:
        pass
    return None
