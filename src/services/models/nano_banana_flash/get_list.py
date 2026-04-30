"""GET List tasks — text-to-image/nano-banana-pro-flash
Docs: https://docs.freepik.com/api-reference/text-to-image/nano-banana-pro-flash/nano-banana-pro-flash-tasks
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations

import logging
from src.services.request_engine import request_engine

logger = logging.getLogger(__name__)

BASE_URL = "https://api.freepik.com/v1/ai"
STATUS_PATH = "text-to-image/nano-banana-pro-flash"


async def list_tasks(api_key: str) -> dict:
    """GET /v1/ai/text-to-image/nano-banana-pro-flash"""
    url = f"{BASE_URL}/{STATUS_PATH}"
    logger.info("[nano_banana_flash] Listing all tasks")
    return await request_engine(method="GET", url=url, force_api_key=api_key)
