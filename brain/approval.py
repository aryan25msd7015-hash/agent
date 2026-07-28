from __future__ import annotations


RISKY_PATTERNS = [
    "delete ",
    "remove ",
    "format ",
    "shutdown",
    "reboot",
    "power off",
    "rm -",
]


def requires_approval(intent: str) -> bool:
    lower = intent.lower()
    return any(p in lower for p in RISKY_PATTERNS)
