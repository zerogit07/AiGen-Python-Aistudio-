"""POST Create task — video/kling-v3-omni-pro
Docs: https://docs.freepik.com/api-reference/video/kling-v3-omni/generate-pro
Response codes: 200, 400, 401, 500, 503
Note: multi_prompt is string[] (NOT object[] like V3)
"""
from __future__ import annotations


ENDPOINT = "video/kling-v3-omni-pro"
STATUS_PATH = "video/kling-v3-omni"
RESOLUTION = "1080"
DURATIONS = ["3", "5", "7", "10", "12", "15"]


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/video/kling-v3-omni-pro"""
    payload: dict = {"prompt": params.prompt}
    int_duration = int(params.duration or "5")
    payload["duration"] = str(int_duration)
    if params.image_base64:
        payload["start_image_url"] = params.image_base64
    elif params.image_url:
        payload["start_image_url"] = params.image_url
    if params.image_url_last:
        payload["end_image_url"] = params.image_url_last
    if params.image_refs:
        payload["elements"] = [
            {"reference_image_urls": params.image_refs[:3]}
        ]
    if params.generate_audio:
        payload["generate_audio"] = True
    if params.shots and params.kling3_mode in ("multi_intelligence", "multi_customize"):
        payload["multi_prompt"] = [
            s.get("prompt", "") for s in params.shots
        ]
        if params.kling3_mode == "multi_intelligence":
            payload["shot_type"] = "intelligent"
        else:
            payload["shot_type"] = "customize"
    return await send_request(ENDPOINT, STATUS_PATH, payload)
