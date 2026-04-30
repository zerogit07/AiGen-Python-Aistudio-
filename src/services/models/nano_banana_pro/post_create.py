"""POST Create task — text-to-image/nano-banana-pro
Docs: https://docs.freepik.com/api-reference/text-to-image/post-nano-banana-pro
Response codes: 200, 400, 401, 500, 503
"""
from __future__ import annotations


ENDPOINT = "text-to-image/nano-banana-pro"
STATUS_PATH = "text-to-image/nano-banana-pro"


async def create_task(params, send_request) -> dict:
    """POST /v1/ai/text-to-image/nano-banana-pro"""
    ratio_map = {
        "widescreen_16_9": "16:9",
        "portrait_9_16": "9:16",
        "square_1_1": "1:1",
    }
    raw_ratio = params.aspect_ratio or "1:1"
    aspect = ratio_map.get(raw_ratio, raw_ratio)

    payload: dict = {"prompt": params.prompt, "aspect_ratio": aspect}
    res_map = {"4k": "4K", "2k": "2K", "1k": "1K"}
    payload["resolution"] = res_map.get(params.resolution, "2K")
    if params.image_refs:
        payload["reference_images"] = [
            {
                "image": url,
                "mime_type": (
                    "image/png"
                    if url.lower().endswith(".png")
                    else "image/webp"
                    if url.lower().endswith(".webp")
                    else "image/jpeg"
                ),
            }
            for url in params.image_refs[:3]
        ]
    return await send_request(ENDPOINT, STATUS_PATH, payload)
