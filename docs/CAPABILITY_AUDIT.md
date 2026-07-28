# Capability Audit — What Works vs What Fails

Test date: live API + orchestrator probes on cloud dev environment (Linux).  
Your production target is **Windows laptop + phone via Telegram**.

## Executive answer

| Capability | Can agent do it today? |
|------------|------------------------|
| Google Drive **web app** navigation (click folders, search UI, download via browser) | **No** (not reliably) |
| Google Drive **API** download by filename | **Yes** (if OAuth credentials configured) |
| Google Drive **desktop app** (Windows installed app) | **No** |
| Desktop **native apps** (Notepad, Excel, Tableau GUI) | **Partial** — only explicit `automate <app>: ...` commands; no natural-language “open Excel and …” |
| Desktop **web apps** in browser (Playwright) | **Partial** — can load pages; Google Drive stops at sign-in; no saved session |
| **Mobile/tablet apps** (Drive app, any local app) | **No** — phone is command-only via Telegram |
| Remote command from phone while laptop runs task | **Partial** — Telegram → API on laptop works if bot+API run on laptop |

---

## Test results (representative)

| Intent | Result | Why |
|--------|--------|-----|
| `download sales_data.csv from gdrive` | **FAIL** without `config/google_client_secret.json` | Drive API OAuth not configured |
| `navigate google drive and download quarterly_report.csv` | Was **chat** fallback; after fix routes to **gdrive** but still needs OAuth | Router required both “gdrive” and “download”; natural language missed |
| `browse https://drive.google.com` | Loads page; title **“Google Drive: Sign-in”** | No Google login in browser automation |
| `browse https://drive.google.com workflow: click=#search` | **FAIL** at action step | Wrong selectors; Drive UI is dynamic/React |
| `automate chrome: hotkey ctrl+l; type drive.google.com` | **dry_run** on Linux; real on Windows with PyAutoGUI | UI engine not executing in headless Linux |
| `open notepad on my android tablet` | **FAIL** (was HTTP 500; now graceful error) | Treated as file path, not device routing |
| `STOP` in Telegram | Bot exits | Kill switch works |
| Connector daemon | Only pings `/health` | Does **not** pull or execute queued tasks |

Automated suite: `python3 -m pytest -q` → 10 passed (mocked/happy paths).

---

## Loose ends (failure modes)

### 1. Google Drive web application

- `browse https://drive.google.com` opens sign-in, not your files.
- No integration between Drive **API OAuth token** and Playwright **browser session**.
- No site-specific workflow for Drive (folder navigation, “My Drive”, shared drives, download button).
- Google often blocks or challenges automated logins (CAPTCHA, 2FA).

**Verdict:** Agent cannot “wander through Google Drive website” like a human today.

**Workable path:** Use Drive API (`skills/download_gdrive.py`) for files; use Playwright only for sites you script with stored session cookies.

### 2. Google Drive desktop application (Windows)

- No skill for “Google Drive for desktop” sync folder or its UI.
- `open_path` only opens existing filesystem paths via `os.startfile` (Windows-only).

**Verdict:** Cannot operate the Drive desktop client.

**Workable path:** Read from local sync folder (`G:\My Drive\...` or `C:\Users\...\Google Drive`) with `list` / `open` on real paths.

### 3. Desktop applications (Windows)

- Natural language like “open Tableau and import CSV” → **chat** fallback or wrong route.
- Desktop control requires: `automate <name>: hotkey ...; type ...; press ...`
- PyAutoGUI only; no **pywinauto** UIA tree, no window targeting, no “find Notepad window”.
- Fragile: resolution, focus, app updates break scripts.

**Verdict:** Not “any desktop app”; only pre-scripted action graphs.

### 4. Mobile / tablet applications

- **Telegram bot** = remote control surface only.
- No Android/iOS agent, no Accessibility API, no MDM, no Appium.
- Commands like “on my phone” are not routed to a mobile executor.

**Verdict:** Cannot navigate apps on phone or tablet locally.

### 5. Architecture gaps

| Component | Gap |
|-----------|-----|
| `connector/runtime/agent.py` | Heartbeat only; no task polling/execution |
| `brain/api.py` | Runs orchestrator inline; no separate “hands” process |
| `brain/graph.py` | Keyword router, not full LangGraph multi-step planner |
| `bot/telegram_bot.py` | No `pending_approval` Y/N flow in chat |
| `config/secrets.py` | Not wired into `settings` for Telegram/Drive secrets |
| `open_url` | Was stub; now opens headless browser but not user’s logged-in Chrome |
| Voice | Whisper runs locally but heavy; no transcript → planner quality tests |

### 6. Environment / ops

- Playwright browsers must be installed: `python3 -m playwright install chromium`
- Ollama often not running → planner degrades to static note JSON
- PyAutoGUI fails or dry-runs on Linux cloud agents (expected)
- Laptop must be on and running API + bot for remote commands

---

## What you can demo reliably today (Windows laptop)

1. Configure `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_USER_ID`, Google OAuth files.
2. Run API + bot on laptop.
3. From phone Telegram:
   - `download myfile.csv from gdrive` (API path)
   - `automate notepad: type hello world`
   - `browse https://example.com` (headless; not your Chrome profile)
4. Risky commands pause for approval via API (`POST /v1/tasks/{id}/approve`), not yet in Telegram UI.

---

## Recommended next build order (to close gaps)

1. **Drive web:** Playwright persistent context + manual one-time login export; or stay API-only.
2. **Connector:** Poll `pending` tasks and execute on device (true remote hands).
3. **Telegram approvals:** When status `pending_approval`, prompt Y/N in chat.
4. **NL → action graph:** Local LLM tool schema for `automate` / `browse` / `download_gdrive`.
5. **Mobile:** Accept “command only” scope, or add Appium for specific apps (high effort).
6. **Desktop apps:** pywinauto window attach + screenshot loop for vision-guided fallback.
