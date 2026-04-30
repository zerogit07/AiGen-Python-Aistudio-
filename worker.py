from __future__ import annotations

import asyncio
import logging
import os
import random

from arq.connections import RedisSettings
from arq.worker import Worker
from dotenv import load_dotenv
from telegram import Bot

load_dotenv(".env.local")
load_dotenv()

from src.core.triple_pool import TriplePool
from src.core.types import Shot, UserState
from src.database.apikeys import api_key_manager
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.proxies import proxy_manager
from src.database.settings import landing_page_manager
from src.database.usage import usage_manager
from src.database.users import user_manager
from src.services.jobs import finalize_job
from src.services.request_engine import RequestEngineHTTPError

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL belum diatur")


def _build_state(state_data: dict | None) -> UserState:
    payload = state_data or {}
    state = UserState()
    for key, value in payload.items():
        if hasattr(state, key):
            setattr(state, key, value)

    state.temp_image_refs = list(payload.get("temp_image_refs", []) or [])
    state.shots = [
        Shot(prompt=item.get("prompt", ""), duration=int(item.get("duration", 5)))
        for item in (payload.get("shots", []) or [])
        if isinstance(item, dict)
    ]
    return state


async def startup(ctx: dict) -> None:
    logger.info("Loading worker resources...")
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

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur")

    bot = Bot(token=bot_token)
    await bot.initialize()

    triple_pool = TriplePool()
    await triple_pool.refresh()

    ctx["bot"] = bot
    ctx["triple_pool"] = triple_pool
    logger.info("Worker ready. Triple sets: %d", len(triple_pool))


async def shutdown(ctx: dict) -> None:
    bot: Bot | None = ctx.get("bot")
    if bot is not None:
        await bot.shutdown()


async def process_generation(
    ctx: dict,
    user_id: int,
    chat_id: int,
    prompt: str,
    model_id: str,
    state_data: dict | None = None,
    status_msg_id: int | None = None,
) -> None:
    await asyncio.sleep(random.uniform(1, 5))

    bot: Bot = ctx["bot"]
    triple_pool: TriplePool = ctx["triple_pool"]
    state = _build_state(state_data)

    if not status_msg_id:
        msg = await bot.send_message(
            chat_id=chat_id,
            text="⏳ *Menyiapkan request AI...*",
            parse_mode="Markdown",
        )
        status_msg_id = msg.message_id

    triple_set = await triple_pool.acquire()
    try:
        await finalize_job(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            state=state,
            prompt=prompt,
            model_id=model_id,
            status_msg_id=status_msg_id,
            triple_set=triple_set,
        )
    except RequestEngineHTTPError as exc:
        if exc.status_code in (403, 429):
            await triple_pool.mark_burned(triple_set)
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text=(
                        f"❌ Error: {exc.status_code} - API menolak request untuk set saat ini. "
                        "Silakan coba lagi beberapa saat lagi."
                    ),
                )
            except Exception:
                pass
            return

        await triple_pool.release(triple_set)
        raise
    except Exception:
        await triple_pool.release(triple_set)
        raise
    else:
        await triple_pool.release(triple_set)


class WorkerSettings:
    functions = [process_generation]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    max_jobs = 5
    max_tries = 1
    job_timeout = 60 * 60


if __name__ == "__main__":
    worker = Worker(
        functions=WorkerSettings.functions,
        on_startup=WorkerSettings.on_startup,
        on_shutdown=WorkerSettings.on_shutdown,
        redis_settings=WorkerSettings.redis_settings,
        max_jobs=WorkerSettings.max_jobs,
        max_tries=WorkerSettings.max_tries,
        job_timeout=WorkerSettings.job_timeout,
    )
    worker.run()
