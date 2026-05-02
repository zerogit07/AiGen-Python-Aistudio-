"""AiGen Studio Bot - Python Edition

Telegram bot that proxies requests to the Freepik AI API for video/image
generation.  Manages multi-model workflows, user subscriptions, and API key
rotation.

Usage:
    python server.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.bot.handlers.callbacks import callback_handler
from src.bot.handlers.commands import admin_command, start_command
from src.bot.handlers.messages import photo_handler, text_handler
from src.bot.state import start_state_cleaner
from src.database.apikeys import api_key_manager
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.proxies import proxy_manager
from src.database.settings import landing_page_manager
from src.database.usage import usage_manager
from src.database.users import user_manager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Load all data from Supabase after bot is initialized."""
    logger.info("Loading data from Supabase...")
    await asyncio.gather(
        api_key_manager.load_keys(),
        member_manager.load_members(),
        member_manager.load_custom_limits(),
        model_manager.load_status(),
        proxy_manager.load_proxies(),
        landing_page_manager.load_settings(),
        usage_manager.load_usage(),
        user_manager.load_users(),
    )
    logger.info("All data loaded successfully.")

    # Clear and re-set bot commands
    try:
        await application.bot.delete_my_commands(read_timeout=20, connect_timeout=20)
        await application.bot.set_my_commands([
            ("start", "Menu Utama"),
            ("admin", "Panel Admin"),
        ], read_timeout=20, connect_timeout=20)
    except Exception as e:
        logger.warning("Failed to set bot commands during startup: %s", e)

    # Start background state cleaner
    asyncio.create_task(start_state_cleaner())

    # Initial proxy check
    result = await proxy_manager.check_all_proxies()
    logger.info(
        "[Proxy] Startup check complete. Active: %d, Dead: %d",
        result["active_count"],
        result["dead_count"],
    )

    logger.info("Bot started using Polling mode (AiGen Studio Python).")


async def periodic_proxy_check(application: Application) -> None:
    """Check proxies every 30 minutes."""
    while True:
        await asyncio.sleep(30 * 60)
        try:
            result = await proxy_manager.check_all_proxies()
            logger.info(
                "[Proxy] Background check. Active: %d, Dead: %d",
                result["active_count"],
                result["dead_count"],
            )
        except Exception as exc:
            logger.error("[Proxy] Background check failed: %s", exc)


from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set! Telegram bot will NOT start.")
    else:
        bot_app = (
            Application.builder()
            .token(bot_token)
            .connect_timeout(20.0)
            .read_timeout(20.0)
            .write_timeout(20.0)
            .pool_timeout(20.0)
            .get_updates_read_timeout(30.0)
            .post_init(post_init)
            .build()
        )

        # Register handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(CommandHandler("admin", admin_command))
        bot_app.add_handler(CallbackQueryHandler(callback_handler))
        bot_app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

        logger.info("Initializing bot application...")
        await bot_app.initialize()
        await bot_app.start()
        try:
            await bot_app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is polling.")
        except Exception as e:
            logger.warning(f"Polling already running or error: {e}")

    yield

    if bot_app:
        logger.info("Shutting down bot application...")
        if bot_app.updater:
            await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

app = FastAPI(lifespan=lifespan, title="AiGen Studio API")

@app.get("/")
async def root():
    return {"message": "AiGen Studio Bot Service is running."}

@app.get("/health")
async def health():
    return {"status": "ok"}

def main() -> None:
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starting FastAPI server on port {port}...")
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
