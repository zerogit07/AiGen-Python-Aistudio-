"""GET Task by ID — image-to-video/kling-o1/{task_id}
Docs: https://docs.freepik.com/api-reference/kling-o1/task-by-id
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "image-to-video/kling-o1"


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/image-to-video/kling-o1/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_o1_std] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
