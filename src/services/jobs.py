from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone

import httpx

from src.core.types import TripleSet, UserState
from src.database.client import supabase
from src.database.members import member_manager
from src.database.usage import usage_manager
from src.services.freepik_api import GenerateParams, submit_video_generation
from src.services.polling import watch_generation
from src.services.request_engine import RequestEngineHTTPError
from src.services.stats import log_activity

logger = logging.getLogger(__name__)


async def finalize_job(
    bot,
    chat_id: int,
    user_id: int,
    state: UserState,
    prompt: str,
    model_id: str,
    status_msg_id: int | None = None,
    triple_set: TripleSet | None = None,
) -> None:
    member_data = member_manager.get_member_data(user_id)
    if not member_data:
        return

    can_start = await member_manager.start_process(user_id, member_data.plan)
    if not can_start:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"*ANTRIAN PENUH*\n\nAnda telah mencapai batas maksimal proses "
                f"simultan untuk paket *{member_data.plan}*. Mohon tunggu salah "
                f"satu proses selesai atau gunakan perintah /reset."
            ),
            parse_mode="Markdown",
        )
        return

    if not status_msg_id:
        msg = await bot.send_message(
            chat_id=chat_id,
            text="⏳ *Menyiapkan request AI...*",
            parse_mode="Markdown",
        )
        status_msg_id = msg.message_id

    try:
        image_base64 = ""
        if state.temp_image_url and state.temp_image_url.startswith("http"):
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text="⏳ Mengirim data...",
                )
            except Exception:
                pass
            async with httpx.AsyncClient() as client:
                resp = await client.get(state.temp_image_url)
                image_base64 = base64.b64encode(resp.content).decode("utf-8")

        image_tail_base64 = ""
        if state.temp_image_url_last:
            async with httpx.AsyncClient() as client:
                resp = await client.get(state.temp_image_url_last)
                image_tail_base64 = base64.b64encode(resp.content).decode("utf-8")

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text="⏳ Mengirim data...",
            )
        except Exception:
            pass

        params = GenerateParams(
            model_id=model_id,
            prompt=prompt,
            duration=state.duration or "5",
            aspect_ratio=state.aspect_ratio or "portrait_9_16",
            orientation=state.orientation,
            image_url=state.temp_image_url,
            video_url=state.temp_video_url,
            image_base64=image_base64,
            mode=state.mode,
            image_url_last=image_tail_base64 or state.temp_image_url_last or "",
            image_refs=state.temp_image_refs,
            kling3_mode=state.kling3_mode,
            shots=[{"prompt": s.prompt, "duration": s.duration} for s in state.shots],
            generate_audio=state.generate_audio,
            resolution=state.resolution or "720",
            camera_config=state.camera_config,
        )

        result = await submit_video_generation(params, triple_set=triple_set)

        if result.get("error"):
            await member_manager.end_process(user_id)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=f"❌ Error: 400 - {result['error']}",
            )
            return

        used_key = result["used_key"]
        final_status_path = result["final_status_path"]
        job_data = result["data"]
        if isinstance(job_data, dict):
            job_data = job_data.get("data", job_data)

        job_id = (
            job_data.get("task_id")
            or job_data.get("id")
            or job_data.get("job_id")
            or job_data.get("jobId")
        )

        if not job_id:
            await member_manager.end_process(user_id)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text="❌ Error: 500 - Gagal mendapatkan Task ID dari API.",
            )
            return

        if supabase:
            try:
                await supabase.table("jobs").insert(
                    {
                        "job_id": str(job_id),
                        "user_id": str(user_id),
                        "model_id": model_id,
                        "status": "processing",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).execute()
            except Exception as exc:
                logger.error("Error inserting job to DB: %s", exc)

        log_activity(user_id, model_id, prompt)
        await usage_manager.increment_usage(user_id)

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text="⏳ Menunggu hasil generate...",
            )
        except Exception:
            pass

        await watch_generation(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            job_id=str(job_id),
            status_path=final_status_path,
            status_msg_id=status_msg_id,
            prompt=prompt,
            used_key=used_key,
            original_model_id=model_id,
            triple_set=triple_set,
        )

    except RequestEngineHTTPError:
        await member_manager.end_process(user_id)
        raise
    except Exception as exc:
        await member_manager.end_process(user_id)
        logger.error("Error in finalize_job: %s", exc)
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=f"❌ Error: {exc}",
            )
        except Exception:
            pass
        raise
