from __future__ import annotations

import json
import os
from typing import Any

import httpx

from brain.audit import audit_log
from brain.graph import build_router
from brain.memory.chroma_store import MemoryStore
from brain.memory.prefs import PrefStore
from brain.planner import plan_action_graph
from config.allowlist import assert_path_allowed
from config.settings import settings
from connector.mobile.appium_stub import AppiumConnector
from skills.action_graph import parse_action_graph
from skills.browser_automation import (
    bootstrap_google_login,
    google_drive_web_download,
    open_url,
    run_workflow,
)
from skills.build_tableau import build_twbx_from_template
from skills.download_gdrive import download_file_by_name, search_files
from skills.dropbox_skill import download_dropbox_file
from skills.onedrive import download_onedrive_file
from skills.power import keep_awake_windows, wake_on_lan
from skills.registry import list_dir, open_path
from skills.ui_automation import UIAutomationEngine
from skills.vision_agent import VisionGuidedAgent


class Orchestrator:
    def __init__(self) -> None:
        self.ui = UIAutomationEngine()
        self.router = build_router()
        self.memory = MemoryStore()
        self.prefs = PrefStore()
        self.vision = VisionGuidedAgent()
        self.appium = AppiumConnector()

    def run(self, intent: str) -> dict[str, Any]:
        audit_log.write("intent", {"intent": intent})
        lower = intent.lower()
        route_state = self.router.invoke({"intent": intent, "route": ""})
        route = route_state["route"]
        app, steps = parse_action_graph(intent)

        if route == "ui_automation" and app and steps:
            execution = self.ui.execute(app, steps, verify=True)
            result = {"action": "ui_automation", "app": app, "execution": execution}
            audit_log.write("result", result)
            return result

        if lower.startswith("vision "):
            goal = intent[7:].strip()
            result = self.vision.run(goal)
            audit_log.write("result", result)
            return result

        if lower.startswith("keep awake"):
            result = keep_awake_windows(enable="off" not in lower)
            audit_log.write("result", result)
            return {"action": "keep_awake", **result}

        if lower.startswith("wake "):
            mac = intent.split(" ", maxsplit=1)[1].strip()
            result = wake_on_lan(mac, os.getenv("WOL_BROADCAST_IP"))
            audit_log.write("result", result)
            return {"action": "wake_on_lan", **result}

        if "android" in lower or "appium" in lower:
            result = self.appium.run_intent(intent)
            audit_log.write("result", result)
            return result

        if route == "browser" and lower.startswith("browse "):
            url = intent[7:].strip()
            if "drive.google.com" in url and "download" in lower:
                query = self._guess_drive_query(intent)
                # Prefer API first even for browse+download phrasing.
                result = self._drive_api_then_web(query)
                audit_log.write("result", result)
                return result
            if "workflow:" in url:
                target, workflow = url.split("workflow:", maxsplit=1)
                actions = self._parse_workflow(workflow.strip())
                result = run_workflow(target.strip(), actions=actions)
                audit_log.write("result", result)
                return result
            result = open_url(url)
            audit_log.write("result", result)
            return result

        if lower.startswith("drive login bootstrap"):
            result = bootstrap_google_login(settings.drive_playwright_user_data_dir, headless=True)
            audit_log.write("result", result)
            return result

        if route == "gdrive":
            filename = self._guess_drive_query(intent)
            result = self._drive_api_then_web(filename)
            audit_log.write("result", result)
            return result

        if route == "onedrive":
            filename = self._guess_drive_query(intent)
            result = download_onedrive_file(filename, settings.default_download_dir)
            audit_log.write("result", result)
            return result

        if route == "dropbox":
            filename = self._guess_drive_query(intent)
            result = download_dropbox_file(filename, settings.default_download_dir)
            audit_log.write("result", result)
            return result

        if route == "tableau":
            filename = self._guess_drive_query(intent)
            try:
                csv_path = download_file_by_name(
                    filename=filename,
                    output_dir=settings.default_download_dir,
                    credentials_file=settings.drive_credentials_file,
                    token_file=settings.drive_token_file,
                )
                twbx = build_twbx_from_template(csv_path, "skills/templates/default.twb", settings.default_output_dir)
            except Exception as exc:
                result = {"action": "build_tableau", "status": "failed", "error": str(exc)}
                audit_log.write("result", result)
                return result
            self.prefs.set("last_tableau_output", twbx)
            result = {"action": "build_tableau", "csv_path": csv_path, "twbx": twbx}
            audit_log.write("result", result)
            return result

        if lower.startswith("open "):
            target = intent[5:].strip()
            planned_open = plan_action_graph(intent)
            if planned_open:
                app, steps = parse_action_graph(planned_open)
                if app and steps:
                    execution = self.ui.execute(app, steps, verify=True)
                    result = {
                        "action": "ui_automation",
                        "planned_from": intent,
                        "command": planned_open,
                        "app": app,
                        "execution": execution,
                    }
                    audit_log.write("result", result)
                    return result
            try:
                assert_path_allowed(target)
                result = {"action": "open_path", "result": open_path(target)}
            except (FileNotFoundError, PermissionError) as exc:
                result = {"action": "open_path", "status": "failed", "error": str(exc)}
            audit_log.write("result", result)
            return result

        if lower.startswith("list "):
            target = intent[5:].strip()
            try:
                assert_path_allowed(target)
                result = {"action": "list_dir", "result": list_dir(target)}
            except (FileNotFoundError, PermissionError) as exc:
                result = {"action": "list_dir", "status": "failed", "error": str(exc)}
            audit_log.write("result", result)
            return result

        planned = plan_action_graph(intent)
        if planned:
            app, steps = parse_action_graph(planned)
            if app and steps:
                execution = self.ui.execute(app, steps, verify=True)
                result = {
                    "action": "ui_automation",
                    "planned_from": intent,
                    "command": planned,
                    "app": app,
                    "execution": execution,
                }
                audit_log.write("result", result)
                return result

        summary = self._ollama_summary(intent)
        result = {"action": "chat", "result": summary}
        audit_log.write("result", result)
        return result

    def _drive_api_then_web(self, filename: str) -> dict[str, Any]:
        self.memory.add_fact(f"dataset:{filename}", f"Drive dataset requested: {filename}", {"kind": "dataset"})
        try:
            candidates = search_files(
                query=filename,
                credentials_file=settings.drive_credentials_file,
                token_file=settings.drive_token_file,
                limit=5,
            )
            path = download_file_by_name(
                filename=filename,
                output_dir=settings.default_download_dir,
                credentials_file=settings.drive_credentials_file,
                token_file=settings.drive_token_file,
            )
            self.prefs.set("last_download_path", path)
            return {
                "action": "download_gdrive",
                "method": "api",
                "path": path,
                "candidates": candidates,
            }
        except Exception as api_exc:
            web = google_drive_web_download(
                query=filename,
                download_dir=settings.default_download_dir,
                user_data_dir=settings.drive_playwright_user_data_dir,
                headless=True,
            )
            web["api_error"] = str(api_exc)
            web["fallback"] = "web"
            if web.get("status") == "executed" and web.get("path"):
                self.prefs.set("last_download_path", web["path"])
            return web

    def _guess_filename(self, intent: str) -> str:
        for token in intent.replace('"', " ").replace("'", " ").split():
            if token.endswith((".csv", ".xlsx", ".json", ".pdf", ".docx")):
                return token
        return "sales_data.csv"

    def _guess_drive_query(self, intent: str) -> str:
        explicit = self._guess_filename(intent)
        if explicit != "sales_data.csv":
            return explicit
        text = intent.lower()
        if "download" in text:
            after = text.split("download", maxsplit=1)[1].strip()
            for stop in [" from ", " in ", " on ", " using "]:
                if stop in after:
                    after = after.split(stop, maxsplit=1)[0].strip()
            if after:
                return after
        return "sales_data"

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
