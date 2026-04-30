"""GET List tasks — text-to-video/veo-3-1-fast
Docs: https://docs.freepik.com/api-reference/text-to-video/get-veo-3-1-fast
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "text-to-video/veo-3-1-fast"


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/text-to-video/veo-3-1-fast"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[veo_3_1_fast] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)
