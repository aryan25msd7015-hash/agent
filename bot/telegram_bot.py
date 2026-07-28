from __future__ import annotations

import asyncio
import tempfile

import httpx
from faster_whisper import WhisperModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config.settings import settings

_whisper_model: WhisperModel | None = None
API = "http://127.0.0.1:8787"


def _transcribe_voice(path: str) -> str:
    global _whisper_model
    try:
        if _whisper_model is None:
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = _whisper_model.transcribe(path)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text or "voice command"
    except Exception:
        return "voice command"


async def _authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) == settings.telegram_allowed_user_id)


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    await update.message.reply_text("Personal agent online. Send a task.")


async def handle_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    intent = (update.message.text or "").strip()
    if intent.upper() == "STOP":
        await update.message.reply_text("Kill-switch activated. Manual restart required.")
        raise SystemExit(0)
    if intent.upper() == "START":
        await update.message.reply_text("Agent accepting commands.")
        return
    await _handle_intent(update, intent)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    voice = update.message.voice
    if not voice:
        return
    with tempfile.TemporaryDirectory() as td:
        path = f"{td}/voice.ogg"
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(path)
        transcript = await asyncio.to_thread(_transcribe_voice, path)
        await update.message.reply_text(f"Voice transcript: {transcript}")
        await _handle_intent(update, transcript)


async def handle_approval_callback(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update):
        return
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    parts = query.data.split(":", maxsplit=2)
    if len(parts) != 3 or parts[0] != "approve":
        return
    _, decision, task_id = parts
    approved = decision == "yes"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{API}/v1/tasks/{task_id}/approve", json={"approved": approved})
        r.raise_for_status()
        body = r.json()
    status = body.get("status")
    if status == "queued":
        await query.edit_message_text(f"Approved. Task {task_id} queued for connector.")
        final = await _wait_for_terminal(task_id)
        await query.message.reply_text(final)
    elif status == "cancelled":
        await query.edit_message_text(f"Denied. Task {task_id} cancelled.")
    else:
        await query.edit_message_text(f"Task {task_id} → {status}: {body.get('result')}")


async def _handle_intent(update: Update, intent: str) -> None:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{API}/v1/tasks",
            json={"intent": intent, "target_device": "windows-laptop", "dispatch": True},
        )
        r.raise_for_status()
        body = r.json()
    task_id = body["task_id"]
    status = body["status"]
    if status == "pending_approval":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Approve", callback_data=f"approve:yes:{task_id}"),
                    InlineKeyboardButton("Deny", callback_data=f"approve:no:{task_id}"),
                ]
            ]
        )
        await update.message.reply_text(
            f"Approval required for task {task_id}:\n{intent}",
            reply_markup=keyboard,
        )
        return
    if status == "queued":
        await update.message.reply_text(f"Queued {task_id}. Waiting for connector…")
        final = await _wait_for_terminal(task_id)
        await update.message.reply_text(final)
        return
    await update.message.reply_text(f"Task {task_id} {status}: {body.get('result')}")


async def _wait_for_terminal(task_id: str, timeout_s: int = 180) -> str:
    deadline = asyncio.get_event_loop().time() + timeout_s
    async with httpx.AsyncClient(timeout=30) as client:
        while asyncio.get_event_loop().time() < deadline:
            r = await client.get(f"{API}/v1/tasks/{task_id}")
            r.raise_for_status()
            body = r.json()
            status = body.get("status")
            if status in {"completed", "failed", "cancelled"}:
                return f"Task {task_id} {status}: {body.get('result')}"
            await asyncio.sleep(1.5)
    return f"Task {task_id} still running (timeout). Check /v1/tasks/{task_id}"


def run() -> None:
    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()


if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run))
