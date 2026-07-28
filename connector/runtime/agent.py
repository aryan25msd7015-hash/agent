from __future__ import annotations

import argparse
import time
from typing import Any

import httpx

from brain.orchestrator import Orchestrator
from skills.power import keep_awake_windows


class ConnectorAgent:
    def __init__(self, base_url: str, device_id: str = "windows-laptop", poll_seconds: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.poll_seconds = poll_seconds
        self.orch = Orchestrator()

    def loop(self) -> None:
        keep_awake_windows(True)
        print(f"Connector online for device={self.device_id}. Claiming queued tasks.")
        while True:
            try:
                self._tick()
            except Exception as exc:
                print(f"Connector tick error: {exc}")
            time.sleep(self.poll_seconds)

    def _tick(self) -> None:
        with httpx.Client(timeout=30) as client:
            health = client.get(f"{self.base_url}/health")
            health.raise_for_status()
            claimed = client.get(f"{self.base_url}/v1/devices/{self.device_id}/tasks/next")
            claimed.raise_for_status()
            payload = claimed.json()
            task = payload.get("task")
            if not task:
                return
            task_id = task["id"]
            intent = task["intent"]
            print(f"Claimed task {task_id}: {intent}")
            try:
                result: dict[str, Any] = self.orch.run(intent)
                status = "failed" if result.get("status") == "failed" else "completed"
            except Exception as exc:
                result = {"action": "connector_error", "error": str(exc)}
                status = "failed"
            client.post(
                f"{self.base_url}/v1/tasks/{task_id}/result",
                json={"status": status, "result": result},
            ).raise_for_status()
            print(f"Reported {status} for {task_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--device-id", default="windows-laptop")
    parser.add_argument("--poll-seconds", type=int, default=2)
    args = parser.parse_args()
    ConnectorAgent(args.base_url, args.device_id, args.poll_seconds).loop()
