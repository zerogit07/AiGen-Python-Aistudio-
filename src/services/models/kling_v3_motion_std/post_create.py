"""POST Create task — video/kling-v3-motion-control-std
Docs: https://docs.freepik.com/api-reference/video/kling-v3-motion-control/generate-std
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations


ENDPOINT = "video/kling-v3-motion-control-std"
STATUS_PATH = "video/kling-v3-motion-control-std"
RESOLUTION = "720"


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/video/kling-v3-motion-control-std"""
    payload: dict = {}
    if params.prompt:
        payload["prompt"] = params.prompt
    if params.image_base64:
        payload["image_url"] = params.image_base64
    elif params.image_url:
        payload["image_url"] = params.image_url
    if params.video_url:
        payload["video_url"] = params.video_url
    payload["character_orientation"] = params.orientation or "video"
    return await send_request(ENDPOINT, STATUS_PATH, payload)
