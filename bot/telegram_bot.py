from __future__ import annotations

import asyncio
import tempfile

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config.settings import settings


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
    result = await _submit(intent)
    await update.message.reply_text(result)


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
        # Placeholder transcript until local whisper wiring is expanded.
        result = await _submit("voice command received")
        await update.message.reply_text(f"Voice accepted. {result}")


async def _submit(intent: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("http://127.0.0.1:8787/v1/tasks", json={"intent": intent, "target_device": "windows-laptop"})
        r.raise_for_status()
        body = r.json()
        return f"Task {body['task_id']} completed: {body['result']}"


def run() -> None:
    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()


if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run))
