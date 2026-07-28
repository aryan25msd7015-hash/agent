# Personal Agent (Windows-first, local-private)

This repository contains a personal automation agent that:

- accepts commands from Telegram (text/voice placeholder),
- routes intent through a local orchestrator,
- runs actions on your Windows machine,
- supports Google Drive fetches and a Tableau `.twbx` packaging flow.
- supports universal desktop/browser automation intents via action graphs.

## Architecture

- `brain/`: FastAPI gateway + task store + orchestrator
- `bot/`: Telegram command interface
- `connector/`: local connector heartbeat daemon
- `skills/`: actionable tools (Google Drive download, Tableau package, open/list path)

## Quick start

1. Create virtual env and install dependencies:
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate` (Windows)
   - `pip install -e .`
2. Configure env vars:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_TELEGRAM_USER_ID`
   - `GOOGLE_CREDENTIALS_FILE`
3. Start API:
   - `python -m uvicorn brain.api:app --host 127.0.0.1 --port 8787`
4. Start Telegram bot:
   - `python bot/telegram_bot.py`
5. Optional helper:
   - `deploy/start_agent.ps1`

## Notes

- Local LLM endpoint defaults to Ollama at `http://127.0.0.1:11434`.
- `STOP` sent in Telegram triggers kill switch for bot process.
- Tableau flow currently packages template + dataset into `.twbx`.
- Universal automation format:
  - `automate chrome: hotkey ctrl+l; type https://example.com; press enter`
  - `browse https://example.com`