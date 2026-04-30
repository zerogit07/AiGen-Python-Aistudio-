from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from src.core.types import Shot, UserState

logger = logging.getLogger(__name__)

_redis_pool: ArqRedis | None = None
_pool_lock = asyncio.Lock()


def _serialize_state(state: UserState | dict[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {}
    if isinstance(state, dict):
        return dict(state)

    return {
        "duration": state.duration,
        "aspect_ratio": state.aspect_ratio,
        "orientation": state.orientation,
        "temp_image_url": state.temp_image_url,
        "temp_image_url_last": state.temp_image_url_last,
        "temp_image_refs": list(state.temp_image_refs),
        "temp_video_url": state.temp_video_url,
        "mode": state.mode,
        "kling3_mode": state.kling3_mode,
        "shots": [
            {"prompt": shot.prompt, "duration": shot.duration}
            for shot in state.shots
            if isinstance(shot, Shot)
        ]
        or [
            {
                "prompt": getattr(shot, "prompt", "") if not isinstance(shot, dict) else shot.get("prompt", ""),
                "duration": getattr(shot, "duration", 5) if not isinstance(shot, dict) else shot.get("duration", 5),
            }
            for shot in state.shots
        ],
        "generate_audio": state.generate_audio,
        "resolution": state.resolution,
        "camera_config": state.camera_config,
    }


async def _get_redis_pool() -> ArqRedis:
    global _redis_pool
    if _redis_pool is not None:
        return _redis_pool

    async with _pool_lock:
        if _redis_pool is None:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                raise RuntimeError("REDIS_URL belum diatur")
            _redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
        return _redis_pool


async def add_check_keys_job(admin_id: int, chat_id: int) -> str:
    redis = await _get_redis_pool()
    job = await redis.enqueue_job(
        "process_check_keys",
        admin_id=admin_id,
        chat_id=chat_id,
    )
    if job is None:
        raise RuntimeError("Gagal memasukkan job ke antrian")

    logger.info("Check keys job queued: %s for admin %s", job.job_id, admin_id)
    return job.job_id


async def add_job(
    user_id: int,
    chat_id: int,
    prompt: str,
    model_id: str,
    state: UserState | dict[str, Any] | None = None,
    status_msg_id: int | None = None,
) -> str:
    redis = await _get_redis_pool()
    job = await redis.enqueue_job(
        "process_generation",
        user_id=user_id,
        chat_id=chat_id,
        prompt=prompt,
        model_id=model_id,
        state_data=_serialize_state(state),
        status_msg_id=status_msg_id,
    )
    if job is None:
        raise RuntimeError("Gagal memasukkan job ke antrian")

    logger.info("Job queued: %s for user %s", job.job_id, user_id)
    return job.job_id
