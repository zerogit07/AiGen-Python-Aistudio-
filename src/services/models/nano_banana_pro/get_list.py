"""GET List tasks — text-to-image/nano-banana-pro
Docs: https://docs.freepik.com/api-reference/text-to-image/get-nano-banana-pro
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "text-to-image/nano-banana-pro"


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/text-to-image/nano-banana-pro"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[nano_banana_pro] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)
