"""GET Task by ID — video/kling-v3-omni/{task_id}
Docs: https://docs.freepik.com/api-reference/video/kling-v3-omni/task-by-id
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "video/kling-v3-omni"


async def get_task(task_id: str, api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-omni/{task_id}"""
    url = f"{BASE_URL}/{STATUS_PATH}/{task_id}"
    logger.info("[kling_v3_omni_pro] Getting task status: %s", task_id)
    return await request_engine(method="GET", url=url, force_api_key=api_key)
