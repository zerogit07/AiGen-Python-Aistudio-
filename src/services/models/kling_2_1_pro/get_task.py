"""GET Task by ID — image-to-video/kling-v2-1-pro/{task_id}
Docs: https://docs.freepik.com/api-reference/image-to-video/kling-v2.1-pro/get-kling-v2-1-pro-task
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "image-to-video/kling-v2-1-pro"


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-v2-1-pro/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_2_1_pro] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
