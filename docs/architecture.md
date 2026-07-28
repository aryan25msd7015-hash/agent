# Personal Agent Architecture

## Goal

A private, single-user agent that can receive mobile commands, plan locally, and execute tasks across desktop and web apps on Windows.

## Execution strategy

1. API-first tools (Google Drive, web APIs, file operations)
2. App-specific adapters (e.g., Tableau packaging workflow)
3. UI automation fallback (pywinauto/PyAutoGUI) for apps without stable APIs

## Core services

- `brain/api.py`: task API + websocket streams
- `brain/orchestrator.py`: intent routing and model summarization
- `bot/telegram_bot.py`: remote text/voice command ingress
- `connector/runtime/agent.py`: local connector heartbeat daemon

## Safety controls

- Telegram user-id allowlist
- Kill switch (`STOP`)
- Local-only LLM by default (Ollama endpoint)
