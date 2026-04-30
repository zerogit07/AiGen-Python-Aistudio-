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


async def process_check_single_key(ctx: dict, admin_id: int, chat_id: int, api_key: str, key_label: str, batch_id: str) -> None:
    await asyncio.sleep(random.uniform(1, 5))
    
    bot: Bot = ctx["bot"]
    triple_pool: TriplePool = ctx["triple_pool"]
    redis = ctx["redis"]
    
    triple_set = await triple_pool.acquire()
    status_str = "❌ Error Unknown"
    try:
        headers = dict(triple_set.fingerprint)
        headers["x-freepik-api-key"] = api_key
        proxy = triple_set.proxy or None

        import httpx
        async with httpx.AsyncClient(timeout=10, proxy=proxy) as client:
            try:
                resp = await client.head("https://api.freepik.com/v1/resource", headers=headers)
                if resp.status_code == 403:
                    await triple_pool.mark_burned(triple_set)
                    status_str = "❌ 403 Forbidden"
                elif resp.status_code == 429:
                    await triple_pool.mark_burned(triple_set)
                    status_str = "🔒 Rate Limited (429)"
                elif resp.status_code in (200, 404, 400, 405):
                    status_str = "✅ Valid"
                elif resp.status_code == 401:
                    status_str = "❌ Invalid (401)"
                else:
                    status_str = f"❌ Status {resp.status_code}"
                    
            except httpx.RequestError as exc:
                await triple_pool.mark_burned(triple_set)
                status_str = f"❌ Failed (Proxy/Network Error)"

    except Exception as e:
        logger.error("Error checking key %s: %s", key_label, e)
        status_str = f"❌ Failed (Crash)"
    finally:
        if "triple_pool" in locals() and "triple_set" in locals():
            await triple_pool.release(triple_set)
            
        if len(api_key) >= 8:
            masked_key = f"{api_key[:4]}****{api_key[-4:]}"
        else:
            masked_key = "****"

        result_str = f"🔑 {key_label} (`{masked_key}`): {status_str}"

        try:
            await redis.rpush(f"check_batch_results:{batch_id}", result_str)
            current_count = await redis.llen(f"check_batch_results:{batch_id}")
            expected_count_bytes = await redis.get(f"check_batch_total:{batch_id}")
            
            if expected_count_bytes and current_count == int(expected_count_bytes):
                results = await redis.lrange(f"check_batch_results:{batch_id}", 0, -1)
                results_decoded = [res.decode("utf-8") if isinstance(res, bytes) else str(res) for res in results]
                
                def sort_key(text):
                    try:
                        return int(text.split("#")[1].split()[0])
                    except Exception:
                        return 0
                results_decoded.sort(key=sort_key)

                valid_count = sum(1 for r in results_decoded if "✅ Valid" in r)
                limit_count = sum(1 for r in results_decoded if "🔒 Rate Limited (429)" in r)
                invalid_count = len(results_decoded) - valid_count - limit_count

                summary = (
                    f"📊 *Laporan Pengecekan API Key (Selesai)*\n\n"
                    f"- Valid: 🟢 {valid_count}\n"
                    f"- Limit: 🟡 {limit_count}\n"
                    f"- Invalid/Gagal: 🔴 {invalid_count}\n"
                    f"- Total: {len(results_decoded)}\n\n"
                )
                full_text = summary + "\n".join(results_decoded)
                
                if len(full_text) > 4000:
                    for i in range(0, len(full_text), 4000):
                        chunk = full_text[i:i+4000]
                        await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=chat_id, text=full_text, parse_mode="Markdown")
                
                await redis.delete(f"check_batch_results:{batch_id}")
                await redis.delete(f"check_batch_total:{batch_id}")
        except Exception as report_exc:
            logger.error("Gagal mengirim laporan check keys: %s", report_exc)


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
    functions = [process_generation, process_check_single_key]
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
