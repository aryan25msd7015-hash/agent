from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("AGENT_HOST", "127.0.0.1")
    port: int = int(os.getenv("AGENT_PORT", "8787"))
    db_path: str = os.getenv("AGENT_DB_PATH", "data/agent.db")
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_user_id: str = os.getenv("ALLOWED_TELEGRAM_USER_ID", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    drive_credentials_file: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "config/google_client_secret.json")
    drive_token_file: str = os.getenv("GOOGLE_TOKEN_FILE", "config/google_token.json")
    drive_playwright_user_data_dir: str = os.getenv("DRIVE_PLAYWRIGHT_USER_DATA_DIR", "data/playwright-drive-profile")
    drive_playwright_state_file: str = os.getenv("DRIVE_PLAYWRIGHT_STATE_FILE", "config/drive_storage_state.json")
    default_download_dir: str = os.getenv("DEFAULT_DOWNLOAD_DIR", "data/inbox")
    default_output_dir: str = os.getenv("DEFAULT_OUTPUT_DIR", "artifacts")
    laptop_mac_address: str = os.getenv("LAPTOP_MAC_ADDRESS", "")
    allowed_path_roots: str = os.getenv(
        "ALLOWED_PATH_ROOTS",
        "data,artifacts,brain/memory,D:/Agent,D:/Dashboards,C:/Users",
    )


settings = Settings()
