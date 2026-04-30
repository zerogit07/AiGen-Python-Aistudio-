"""POST Create task — image-to-video/kling-v2-1-std
Docs: https://docs.freepik.com/api-reference/image-to-video/kling-v2.1-std/post-kling-v2-1-std
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations


ENDPOINT = "image-to-video/kling-v2-1-std"
STATUS_PATH = "image-to-video/kling-v2-1-std"
RESOLUTION = "720"
DURATIONS = ["5", "10"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/image-to-video/kling-v2-1-std"""
    payload: dict = {}
    int_duration = int(params.duration or "5")
    payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    if params.image_url_last:
        payload["image_tail"] = params.image_url_last
    if params.prompt:
        payload["prompt"] = params.prompt
    return await send_request(ENDPOINT, STATUS_PATH, payload)
