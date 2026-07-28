from __future__ import annotations

import time
import requests


class ConnectorAgent:
    def __init__(self, base_url: str, poll_seconds: int = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_seconds = poll_seconds

    def loop(self) -> None:
        print("Connector online. Waiting for remote tasks.")
        while True:
            try:
                requests.get(f"{self.base_url}/health", timeout=10).raise_for_status()
            except Exception as exc:
                print(f"Gateway unreachable: {exc}")
            time.sleep(self.poll_seconds)


if __name__ == "__main__":
    ConnectorAgent("http://127.0.0.1:8787").loop()
