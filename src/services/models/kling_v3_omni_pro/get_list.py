"""GET List tasks — video/kling-v3-omni
Docs: https://docs.freepik.com/api-reference/video/kling-v3-omni/kling-v3-omni-tasks
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "video/kling-v3-omni"


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/video/kling-v3-omni"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[kling_v3_omni_pro] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)
