"""POST Create task — text-to-video or image-to-video
Docs: https://docs.freepik.com/api-reference/text-to-video/post-veo-3-1
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations


ENDPOINT_TEXT = "text-to-video/veo-3-1"
ENDPOINT_IMAGE = "image-to-video/veo-3-1"
STATUS_PATH_TEXT = "text-to-video/veo-3-1"
STATUS_PATH_IMAGE = "image-to-video/veo-3-1"
DURATIONS = ["4", "6", "8"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/text-to-video/... or /v1/ai/image-to-video/..."""
    ratio_map = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    raw_ratio = params.aspect_ratio or "16:9"
    aspect = ratio_map.get(raw_ratio, raw_ratio)
    int_duration = int(params.duration or "8")
    res_map = {"4k": "4k", "1080": "1080p", "720": "720p"}
    resolution = res_map.get(params.resolution, "720p")

    has_image = params.image_base64 or params.image_url
    endpoint = ENDPOINT_IMAGE if has_image else ENDPOINT_TEXT
    status_path = STATUS_PATH_IMAGE if has_image else STATUS_PATH_TEXT

    payload: dict = {
        "prompt": params.prompt,
        "aspect_ratio": aspect,
        "generate_audio": params.generate_audio,
        "resolution": resolution,
        "duration": int_duration,
    }
    if params.image_base64:
        payload["image"] = params.image_base64
    elif params.image_url:
        payload["image"] = params.image_url
    return await send_request(endpoint, status_path, payload)
