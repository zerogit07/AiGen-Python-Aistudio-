"""Freepik API Router — dispatches to per-model handlers in src/services/models/"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.types import TripleSet
from src.services.request_engine import request_engine
from src.services.models import (
    kling_v3_pro,
    kling_v3_std,
    kling_v3_omni_pro,
    kling_v3_omni_std,
    kling_v3_motion_pro,
    kling_v3_motion_std,
    kling_2_6_pro,
    kling_2_6_motion_pro,
    kling_2_6_motion_std,
    kling_2_5_turbo,
    kling_2_1_pro,
    kling_2_1_std,
    kling_o1_pro,
    kling_o1_std,
    veo_3_1,
    veo_3_1_fast,
    nano_banana_pro,
    nano_banana_flash,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"


@dataclass
class GenerateParams:
    model_id: str
    prompt: str
    aspect_ratio: str = "portrait_9_16"
    resolution: str = "720"
    duration: str = "5"
    generate_audio: bool = True
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url_last: Optional[str] = None
    image_refs: list[str] = field(default_factory=list)
    image_base64: str = ""
    mode: Optional[str] = None
    orientation: Optional[str] = None
    shots: list[dict] = field(default_factory=list)
    kling3_mode: Optional[str] = None
    camera_config: Optional[dict] = None


async def _send_request(
    endpoint: str,
    status_path: str,
    payload: dict,
    triple_set: TripleSet | None = None,
) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    try:
        result = await request_engine(
            method="POST",
            url=url,
            json_data=payload,
            triple_set=triple_set,
        )
        return {
            "data": result["data"],
            "used_key": result["used_key"],
            "final_endpoint": endpoint,
            "final_status_path": status_path,
            "error": None,
        }
    except RuntimeError as exc:
        error_msg = str(exc)
        if error_msg.startswith("400"):
            return {
                "error": error_msg,
                "data": None,
                "used_key": "",
                "final_endpoint": endpoint,
                "final_status_path": status_path,
            }
        raise


# ─── Model Router ─────────────────────────────────────────

MODEL_HANDLERS = {
    # Kling V3
    "kling_v3": kling_v3_pro,
    "kling_v3_pro": kling_v3_pro,
    "kling_v3_std": kling_v3_std,
    # Kling V3 Omni
    "kling_v3_omni": kling_v3_omni_pro,
    "kling_v3_omni_pro": kling_v3_omni_pro,
    "kling_v3_omni_std": kling_v3_omni_std,
    # Kling V3 Motion Control
    "kling_v3_motion": kling_v3_motion_pro,
    "kling_v3_motion_pro": kling_v3_motion_pro,
    "kling_v3_motion_std": kling_v3_motion_std,
    # Kling 2.6
    "kling_2_6_pro": kling_2_6_pro,
    "kling_2_6_motion": kling_2_6_motion_pro,
    "kling_2_6_motion_pro": kling_2_6_motion_pro,
    "kling_2_6_motion_std": kling_2_6_motion_std,
    # Kling 2.5
    "kling_2_5_turbo": kling_2_5_turbo,
    # Kling 2.1
    "kling_2_1": kling_2_1_std,
    "kling_2_1_pro": kling_2_1_pro,
    "kling_2_1_std": kling_2_1_std,
    # Kling O1
    "kling_o1": kling_o1_pro,
    "kling_o1_pro": kling_o1_pro,
    "kling_o1_std": kling_o1_std,
    # Veo 3.1
    "veo_3_1": veo_3_1,
    "veo_3_1_standard": veo_3_1,
    "veo_3_1_fast": veo_3_1_fast,
    "veo_3_1_ingredient": veo_3_1,
    # Nano Banana
    "nano_banana_pro": nano_banana_pro,
    "nano_banana_flash": nano_banana_flash,
}


async def submit_video_generation(
    params: GenerateParams,
    triple_set: TripleSet | None = None,
) -> dict:
    """POST - Create task (generate video/image)."""
    model_id = params.model_id
    module = MODEL_HANDLERS.get(model_id)
    if not module:
        raise RuntimeError(f"Model handler not found for: {model_id}")

    logger.info("[%s] Submitting via %s", model_id, module.__name__)

    async def bound_send_request(endpoint: str, status_path: str, payload: dict) -> dict:
        return await _send_request(
            endpoint=endpoint,
            status_path=status_path,
            payload=payload,
            triple_set=triple_set,
        )

    return await module.create_task(params, bound_send_request)


async def get_task_status(model_id: str, task_id: str, api_key: str) -> dict:
    """GET - Get single task status by task_id."""
    module = MODEL_HANDLERS.get(model_id)
    if not module:
        raise RuntimeError(f"Model handler not found for: {model_id}")
    return await module.get_task(task_id, api_key)


async def list_tasks(model_id: str, api_key: str) -> dict:
    """GET - List all tasks for a model."""
    module = MODEL_HANDLERS.get(model_id)
    if not module:
        raise RuntimeError(f"Model handler not found for: {model_id}")
    return await module.list_tasks(api_key)
