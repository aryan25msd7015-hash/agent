from __future__ import annotations

from typing import Any


def keep_awake_windows(enable: bool = True) -> dict[str, Any]:
    """
    Prevent Windows sleep while agent is running.
    Uses SetThreadExecutionState when available.
    """
    try:
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        if enable:
            ctypes.windll.kernel32.SetThreadExecutionState(  # type: ignore[attr-defined]
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            return {"status": "enabled", "platform": "windows"}
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)  # type: ignore[attr-defined]
        return {"status": "cleared", "platform": "windows"}
    except Exception as exc:
        return {"status": "unsupported", "error": str(exc)}


def wake_on_lan(mac_address: str, ip_address: str | None = None) -> dict[str, Any]:
    try:
        try:
            from wakeonlan import wake as send_magic_packet
        except Exception:
            from wakeonlan import send_magic_packet

        if ip_address:
            send_magic_packet(mac_address, ip_address=ip_address)
        else:
            send_magic_packet(mac_address)
        return {"status": "sent", "mac": mac_address, "ip": ip_address}
    except Exception as exc:
        return {"status": "failed", "error": str(exc), "mac": mac_address}
