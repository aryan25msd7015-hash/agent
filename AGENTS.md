# AGENTS.md

## Cursor Cloud specific instructions

### Overview
Windows-first personal automation agent (Python 3.11+). Core services:
- `brain/` — FastAPI gateway + task store (SQLite) + orchestrator/router (LangGraph). This is the primary, locally-testable service.
- `bot/telegram_bot.py` — Telegram interface. Optional; needs `TELEGRAM_BOT_TOKEN` + `ALLOWED_TELEGRAM_USER_ID` (external service, not runnable in CI without credentials).
- `connector/runtime/agent.py` — local heartbeat daemon. Optional.
- `mcp-servers/*` — Google Drive / Tableau MCP servers. Optional; need Google OAuth credentials.

### Setup / dependencies (fast test startup)
- Dependencies are installed **into the system `python3` (3.12) user site**, not a virtualenv, so `python3 -m pytest -q` works immediately with no activation step.
- The update script runs `python3 -m pip install --user --break-system-packages -e ".[dev]"` (guarded on `pyproject.toml` existing). `--break-system-packages` is required on Ubuntu 24.04 (PEP 668 externally-managed); `--user` installs to `~/.local` which persists in the VM snapshot.
- Heavy deps (chromadb, faster-whisper/onnxruntime, langgraph, google-api-python-client, python-telegram-bot, etc.) are preinstalled in the snapshot, so the boot-time `pip install` is a fast warm re-check (~4s) rather than a cold build (~30s).
- Do **not** create a `.venv`; use `python3`/`pip` directly. Standard package config lives in `pyproject.toml`.

### Lint / test / run
- Lint: `ruff check .` (the repo currently has pre-existing ruff findings; that is expected).
- Test: `python3 -m pytest -q` (7 tests, all offline; `faster-whisper`/Google/Ollama calls are not exercised or are mocked).
- Run API (dev): `python3 -m uvicorn brain.api:app --host 127.0.0.1 --port 8787` then `POST /v1/tasks` with `{"intent": "list ."}`.

### Non-obvious caveats
- Headless-safe: `pyautogui` fails to import without a display, so `UIAutomationEngine` falls back to **dry-run** mode automatically. `automate ...` intents therefore return `dry_run: true` — this is expected in the cloud VM, not a bug.
- The orchestrator calls a local **Ollama** LLM (`http://127.0.0.1:11434`) for generic "chat" intents. Ollama is not installed here; the code catches the connection error and returns a graceful fallback, so `chat` intents still complete. Prefer routed intents (`list `, `open `, `automate `, `browse `, `gdrive download`, `tableau`) for deterministic demos.
- First `Orchestrator()` construction initializes a persistent **ChromaDB** store under `data/chroma/` (auto-created). `data/`, `artifacts/`, and `*.db` are git-ignored.
- Google Drive / Tableau routes require OAuth credentials (`config/google_client_secret.json`); without them those specific routes will error, but the rest of the app runs fine.
