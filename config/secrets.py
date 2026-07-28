from __future__ import annotations

import os


class SecretManager:
    """
    Windows-oriented abstraction:
    - Preferred: system keyring (Credential Manager backend on Windows)
    - Fallback: environment variables
    """

    def __init__(self, service_name: str = "personal-agent") -> None:
        self.service_name = service_name
        try:
            import keyring  # type: ignore

            self._keyring = keyring
        except Exception:
            self._keyring = None

    def get(self, key: str, env_fallback: str | None = None) -> str | None:
        if self._keyring is not None:
            try:
                value = self._keyring.get_password(self.service_name, key)
                if value:
                    return value
            except Exception:
                pass
        if env_fallback:
            return os.getenv(env_fallback)
        return None

    def set(self, key: str, value: str) -> None:
        if self._keyring is None:
            return
        try:
            self._keyring.set_password(self.service_name, key, value)
        except Exception:
            pass
