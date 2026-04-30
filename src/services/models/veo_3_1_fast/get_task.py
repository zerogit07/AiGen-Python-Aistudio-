"""GET Task by ID — text-to-video/veo-3-1-fast/{task_id}
Docs: https://docs.freepik.com/api-reference/text-to-video/get-veo-3-1-fast-task
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "text-to-video/veo-3-1-fast"


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/text-to-video/veo-3-1-fast/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[veo_3_1_fast] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
