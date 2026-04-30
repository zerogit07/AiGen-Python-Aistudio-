"""POST Create task — image-to-video/kling-o1-pro
Docs: https://docs.freepik.com/api-reference/image-to-video/kling-o1-pro
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations


ENDPOINT = "image-to-video/kling-o1-pro"
STATUS_PATH = "image-to-video/kling-o1"
RESOLUTION = "1080"
DURATIONS = ["5", "10"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/image-to-video/kling-o1-pro"""
    ratio_map = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    raw_ratio = params.aspect_ratio or "9:16"
    aspect = ratio_map.get(raw_ratio, raw_ratio)
    int_duration = int(params.duration or "5")

    payload: dict = {
        "prompt": params.prompt,
        "aspect_ratio": aspect,
        "duration": int_duration,
    }
    if params.image_base64:
        payload["first_frame"] = params.image_base64
    elif params.image_url:
        payload["first_frame"] = params.image_url
    if params.image_url_last:
        payload["last_frame"] = params.image_url_last
    return await send_request(ENDPOINT, STATUS_PATH, payload)
