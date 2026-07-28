from __future__ import annotations

"""
Android Appium connector stub.

Real device control requires:
- Appium server
- Android SDK / emulator or USB device
- UiAutomator2 driver

This module provides a safe non-destructive stub so the agent can declare
mobile capability without claiming false execution.
"""

from typing import Any


class AppiumConnector:
    def __init__(self, server_url: str = "http://127.0.0.1:4723") -> None:
        self.server_url = server_url

    def status(self) -> dict[str, Any]:
        return {
            "action": "appium_status",
            "status": "stub",
            "server_url": self.server_url,
            "note": "Install Appium + UiAutomator2 and configure device capabilities to enable.",
        }

    def run_intent(self, intent: str) -> dict[str, Any]:
        return {
            "action": "appium_run",
            "status": "unsupported",
            "intent": intent,
            "error": "Android Appium execution is stubbed. Desktop connector is the active executor.",
            "next_steps": [
                "Install Node Appium server",
                "adb devices",
                "Set ANDROID_CAPABILITIES env JSON",
                "Replace stub with webdriver.Remote session",
            ],
        }
