# AGENTS.md

## Cursor Cloud specific instructions

### Overview
Windows-first personal automation agent (Python 3.11+). Core services:
- `brain/` — FastAPI gateway + task store (SQLite) + orchestrator/router (LangGraph). This is the primary, locally-testable service.
- `bot/telegram_bot.py` — Telegram interface. Optional; needs `TELEGRAM_BOT_TOKEN` + `ALLOWED_TELEGRAM_USER_ID` (external service, not runnable in CI without credentials).
- `connector/runtime/agent.py` — local heartbeat daemon. Optional.
- `mcp-servers/*` — Google Drive / Tableau MCP servers. Optional; need Google OAuth credentials.

### Setup / dependencies
- The update script creates a `.venv` and installs `pip install -e ".[dev]"`. Standard commands live in `pyproject.toml` and `README.md`.
- `python3-venv` (system package) is required to create the virtualenv; it is installed at the OS level, not by the update script.
- Always activate the venv first: `. .venv/bin/activate`.

### Lint / test / run
- Lint: `ruff check .` (the repo currently has pre-existing ruff findings; that is expected).
- Test: `python -m pytest` (7 tests, all offline; `faster-whisper`/Google/Ollama calls are not exercised or are mocked).
- Run API (dev): `python -m uvicorn brain.api:app --host 127.0.0.1 --port 8787` then `POST /v1/tasks` with `{"intent": "list ."}`.

### Non-obvious caveats
- Headless-safe: `pyautogui` fails to import without a display, so `UIAutomationEngine` falls back to **dry-run** mode automatically. `automate ...` intents therefore return `dry_run: true` — this is expected in the cloud VM, not a bug.
- The orchestrator calls a local **Ollama** LLM (`http://127.0.0.1:11434`) for generic "chat" intents. Ollama is not installed here; the code catches the connection error and returns a graceful fallback, so `chat` intents still complete. Prefer routed intents (`list `, `open `, `automate `, `browse `, `gdrive download`, `tableau`) for deterministic demos.
- First `Orchestrator()` construction initializes a persistent **ChromaDB** store under `data/chroma/` (auto-created). `data/`, `artifacts/`, and `*.db` are git-ignored.
- Google Drive / Tableau routes require OAuth credentials (`config/google_client_secret.json`); without them those specific routes will error, but the rest of the app runs fine.
