from __future__ import annotations

import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.types import TripleSet
from src.database.client import supabase
from src.database.members import member_manager
from src.services.request_engine import RequestEngineHTTPError, request_engine

logger = logging.getLogger(__name__)

used_action_buttons: set[str] = set()


def mark_buttons_used(msg_id: int, chat_id: int) -> None:
    used_action_buttons.add(f"{chat_id}:{msg_id}")


async def watch_generation(
    bot,
    chat_id: int,
    user_id: int,
    job_id: str,
    status_path: str,
    status_msg_id: int,
    prompt: str,
    used_key: str,
    original_model_id: str,
    triple_set: TripleSet | None = None,
) -> None:
    """Poll the Freepik API for job completion."""
    retry_count = 0
    max_retries = 180  # 30 minutes (10s * 180)
    finish_again_callback = f"finish_again:{original_model_id}"
    action_key = f"{chat_id}:{status_msg_id}"

    while retry_count < max_retries:
        retry_count += 1
        await asyncio.sleep(10)

        try:
            if status_path == "jobs":
                url = f"https://api.freepik.com/v1/ai/jobs/{job_id}"
            else:
                url = f"https://api.freepik.com/v1/ai/{status_path}/{job_id}"

            logger.info("Polling: %s", url)

            result = await request_engine(
                method="GET",
                url=url,
                force_api_key=None if triple_set else used_key,
                triple_set=triple_set,
            )

            job_data = result["data"].get("data", result["data"])
            status = (job_data.get("status") or "").lower()

            in_progress_statuses = {
                "in_progress", "processing", "queued", "starting",
                "pending", "queued_waiting", "init", "waiting",
            }

            output = job_data.get("output", {})
            result_url = None
            if isinstance(output, dict):
                result_url = output.get("video") or output.get("image") or output.get("url")
            elif isinstance(output, list) and output:
                first = output[0]
                result_url = first.get("url") if isinstance(first, dict) else first

            if not result_url:
                result_data = job_data.get("result", {})
                if isinstance(result_data, dict):
                    result_url = result_data.get("video_url") or result_data.get("image_url")

            if not result_url:
                result_url = job_data.get("video_url") or job_data.get("image_url")

            if not result_url:
                generated = job_data.get("generated", [])
                if generated:
                    result_url = generated[0] if isinstance(generated[0], str) else None

            logger.info("Job %s [%s] Status: %s", job_id, original_model_id, status)

            if status in ("completed", "done", "success") and result_url:
                await member_manager.end_process(user_id)
                if supabase:
                    try:
                        await supabase.table("jobs").update({"status": "completed"}).eq(
                            "job_id", job_id
                        ).execute()
                    except Exception:
                        pass

                is_image_model = "nano_" in original_model_id
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Gunakan Lagi", callback_data=finish_again_callback)],
                    [InlineKeyboardButton("🏠 Ganti Model", callback_data="finish_change")],
                ])

                show_buttons = action_key not in used_action_buttons
                reply_markup = keyboard if show_buttons else None

                try:
                    await bot.delete_message(chat_id=chat_id, message_id=status_msg_id)
                except Exception:
                    pass

                try:
                    if is_image_model:
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=result_url,
                            caption=f"*GENERATE BERHASIL!*\n\nPrompt: {prompt}",
                            parse_mode="Markdown",
                            reply_markup=reply_markup,
                        )
                    else:
                        await bot.send_video(
                            chat_id=chat_id,
                            video=result_url,
                            caption=f"*GENERATE BERHASIL!*\n\nPrompt: {prompt}",
                            parse_mode="Markdown",
                            reply_markup=reply_markup,
                        )
                except Exception:
                    pass

                used_action_buttons.discard(action_key)
                return

            if status in ("failed", "error"):
                await member_manager.end_process(user_id)
                if supabase:
                    try:
                        await supabase.table("jobs").update({"status": "failed"}).eq(
                            "job_id", job_id
                        ).execute()
                    except Exception:
                        pass

                status_code = job_data.get("code", "500")
                error_detail = job_data.get("message", "❌ Generate Gagal")
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg_id,
                        text=f"❌ Error: {status_code} - {error_detail}",
                    )
                except Exception:
                    pass
                used_action_buttons.discard(action_key)
                return

            if status in in_progress_statuses:
                continue

        except RequestEngineHTTPError as exc:
            if exc.status_code in (403, 429):
                raise
            logger.error("Polling HTTP error for job %s: %s", job_id, exc)
        except Exception as exc:
            logger.error("Polling error for job %s: %s", job_id, exc)

    await member_manager.end_process(user_id)
    if supabase:
        try:
            await supabase.table("jobs").update({"status": "failed"}).eq(
                "job_id", job_id
            ).execute()
        except Exception:
            pass
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg_id,
            text="❌ Error: 408 - Timeout. Job tidak selesai dalam 30 menit.",
        )
    except Exception:
        pass
    used_action_buttons.discard(action_key)


poll_job_status = watch_generation
