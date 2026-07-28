from __future__ import annotations

import json
from typing import Any

import httpx

from brain.graph import build_router
from brain.memory.chroma_store import MemoryStore
from brain.memory.prefs import PrefStore
from config.settings import settings
from skills.action_graph import parse_action_graph
from skills.browser_automation import open_url, run_workflow
from skills.build_tableau import build_twbx_from_template
from skills.download_gdrive import download_file_by_name
from skills.registry import list_dir, open_path
from skills.ui_automation import UIAutomationEngine


class Orchestrator:
    def __init__(self) -> None:
        self.ui = UIAutomationEngine()
        self.router = build_router()
        self.memory = MemoryStore()
        self.prefs = PrefStore()

    def run(self, intent: str) -> dict[str, Any]:
        lower = intent.lower()
        route_state = self.router.invoke({"intent": intent, "route": ""})
        route = route_state["route"]
        app, steps = parse_action_graph(intent)
        if route == "ui_automation" and app and steps:
            execution = self.ui.execute(app, steps)
            return {"action": "ui_automation", "app": app, "execution": execution}
        if route == "browser" and lower.startswith("browse "):
            url = intent[7:].strip()
            if "workflow:" in url:
                # Format: browse <url> workflow: click=#id,fill=#q:hello
                target, workflow = url.split("workflow:", maxsplit=1)
                actions = self._parse_workflow(workflow.strip())
                return run_workflow(target.strip(), actions=actions)
            return open_url(url)
        if route == "gdrive":
            filename = self._guess_filename(intent)
            self.memory.add_fact(f"dataset:{filename}", f"Google Drive dataset requested: {filename}", {"kind": "dataset"})
            path = download_file_by_name(
                filename=filename,
                output_dir=settings.default_download_dir,
                credentials_file=settings.drive_credentials_file,
                token_file=settings.drive_token_file,
            )
            self.prefs.set("last_download_path", path)
            return {"action": "download_gdrive", "path": path}
        if route == "tableau":
            filename = self._guess_filename(intent)
            csv_path = download_file_by_name(
                filename=filename,
                output_dir=settings.default_download_dir,
                credentials_file=settings.drive_credentials_file,
                token_file=settings.drive_token_file,
            )
            twbx = build_twbx_from_template(csv_path, "skills/templates/default.twb", settings.default_output_dir)
            self.prefs.set("last_tableau_output", twbx)
            self.memory.add_fact(
                f"tableau:{filename}",
                f"Generated Tableau package from {filename}: {twbx}",
                {"kind": "tableau_output"},
            )
            return {"action": "build_tableau", "csv_path": csv_path, "twbx": twbx}
        if lower.startswith("open "):
            return {"action": "open_path", "result": open_path(intent[5:].strip())}
        if lower.startswith("list "):
            return {"action": "list_dir", "result": list_dir(intent[5:].strip())}
        summary = self._ollama_summary(intent)
        return {"action": "chat", "result": summary}

    def _guess_filename(self, intent: str) -> str:
        for token in intent.replace('"', " ").replace("'", " ").split():
            if token.endswith((".csv", ".xlsx", ".json")):
                return token
        return "sales_data.csv"

    def _ollama_summary(self, intent: str) -> str:
        payload = {"model": settings.ollama_model, "prompt": f"Summarize intent in 1 line: {intent}", "stream": False}
        try:
            res = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=30)
            res.raise_for_status()
            body = res.json()
            return body.get("response", "Could not parse model output").strip()
        except Exception:
            return json.dumps({"note": "Ollama not reachable. Task accepted for future execution."})

    def _parse_workflow(self, workflow: str) -> list[dict[str, str]]:
        actions: list[dict[str, str]] = []
        for raw in [x.strip() for x in workflow.split(",") if x.strip()]:
            if "=" not in raw:
                continue
            left, right = raw.split("=", maxsplit=1)
            kind = left.strip().lower()
            if ":" in right:
                selector, value = right.split(":", maxsplit=1)
            else:
                selector, value = right, ""
            if kind in {"click", "fill", "press"}:
                actions.append({"type": kind, "selector": selector.strip(), "value": value.strip()})
        return actions
