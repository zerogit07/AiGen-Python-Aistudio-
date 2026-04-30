from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    endpoint: str
    status_path: str
    needs_duration: bool
    durations: list[str] = field(default_factory=list)
    needs_orientation: bool = False
    needs_aspect_ratio: bool = False
    resolution: str = ""  # "720" for Std, "1080" for Pro


MODEL_CONFIG: dict[str, ModelConfig] = {
    "kling_v3": ModelConfig(
        endpoint="video/kling-v3-pro",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_motion": ModelConfig(
        endpoint="video/kling-v3-motion-control-pro",
        status_path="video/kling-v3-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_v3_omni": ModelConfig(
        endpoint="video/kling-v3-omni-pro",
        status_path="video/kling-v3-omni",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_pro": ModelConfig(
        endpoint="video/kling-v3-pro",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_std": ModelConfig(
        endpoint="video/kling-v3-std",
        status_path="video/kling-v3",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="720",
    ),
    "kling_v3_motion_pro": ModelConfig(
        endpoint="video/kling-v3-motion-control-pro",
        status_path="video/kling-v3-motion-control-pro",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_v3_motion_std": ModelConfig(
        endpoint="video/kling-v3-motion-control-std",
        status_path="video/kling-v3-motion-control-std",
        needs_duration=False,
        needs_orientation=True,
        resolution="720",
    ),
    "kling_v3_omni_pro": ModelConfig(
        endpoint="video/kling-v3-omni-pro",
        status_path="video/kling-v3-omni",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="1080",
    ),
    "kling_v3_omni_std": ModelConfig(
        endpoint="video/kling-v3-omni-std",
        status_path="video/kling-v3-omni",
        needs_duration=True,
        durations=["3", "5", "7", "10", "12", "15"],
        resolution="720",
    ),
    "kling_2_6_pro": ModelConfig(
        endpoint="image-to-video/kling-v2-6-pro",
        status_path="image-to-video/kling-v2-6",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_6_motion": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-pro",
        status_path="image-to-video/kling-v2-6",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_2_6_motion_pro": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-pro",
        status_path="image-to-video/kling-v2-6",
        needs_duration=False,
        needs_orientation=True,
        resolution="1080",
    ),
    "kling_2_6_motion_std": ModelConfig(
        endpoint="video/kling-v2-6-motion-control-std",
        status_path="image-to-video/kling-v2-6",
        needs_duration=False,
        needs_orientation=True,
        resolution="720",
    ),
    "kling_2_5_turbo": ModelConfig(
        endpoint="image-to-video/kling-v2-5-pro",
        status_path="image-to-video/kling-v2-5-pro",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_1_pro": ModelConfig(
        endpoint="image-to-video/kling-v2-1-pro",
        status_path="image-to-video/kling-v2-1-pro",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_2_1": ModelConfig(
        endpoint="image-to-video/kling-v2-1-std",
        status_path="image-to-video/kling-v2-1-std",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "kling_2_1_std": ModelConfig(
        endpoint="image-to-video/kling-v2-1-std",
        status_path="image-to-video/kling-v2-1-std",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "kling_o1": ModelConfig(
        endpoint="image-to-video/kling-o1-pro",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_o1_pro": ModelConfig(
        endpoint="image-to-video/kling-o1-pro",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="1080",
    ),
    "kling_o1_std": ModelConfig(
        endpoint="image-to-video/kling-o1-std",
        status_path="image-to-video/kling-o1",
        needs_duration=True,
        durations=["5", "10"],
        resolution="720",
    ),
    "veo_3_1": ModelConfig(
        endpoint="text-to-video/veo-3-1",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_standard": ModelConfig(
        endpoint="text-to-video/veo-3-1",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_fast": ModelConfig(
        endpoint="text-to-video/veo-3-1-fast",
        status_path="text-to-video/veo-3-1-fast",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "veo_3_1_ingredient": ModelConfig(
        endpoint="text-to-video/veo-3-1-ingredient",
        status_path="text-to-video/veo-3-1",
        needs_duration=True,
        durations=["4", "6", "8"],
    ),
    "nano_banana_flash": ModelConfig(
        endpoint="text-to-image/nano-banana-pro-flash",
        status_path="text-to-image/nano-banana-pro-flash",
        needs_duration=False,
        needs_aspect_ratio=True,
    ),
    "nano_banana_pro": ModelConfig(
        endpoint="text-to-image/nano-banana-pro",
        status_path="text-to-image/nano-banana-pro",
        needs_duration=False,
        needs_aspect_ratio=True,
    ),
}

DEFAULT_MODELS = [
    {"id": "kling_v3", "name": "\U0001f525 Kling V3"},
    {"id": "kling_v3_motion", "name": "\U0001f525 Kling V3 Motion"},
    {"id": "kling_v3_omni", "name": "\U0001f525 Kling V3 Omni"},
    {"id": "kling_2_6_pro", "name": "\U0001f3ac Kling 2.6 Pro"},
    {"id": "kling_2_6_motion", "name": "\U0001f3ac Kling 2.6 Motion"},
    {"id": "kling_2_5_turbo", "name": "\U0001f680 Kling 2.5 Turbo"},
    {"id": "kling_2_1", "name": "\U0001f3ac Kling 2.1"},
    {"id": "kling_o1", "name": "\u2728 Kling O1"},
    {"id": "veo_3_1", "name": "\U0001f3a5 Veo 3.1"},
    {"id": "nano_banana_flash", "name": "\U0001f34c Nano Banana"},
]

FINGERPRINTS: list[dict[str, str]] = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.8,id;q=0.6",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.7",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept-Language": "en-AU,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.2478.67 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-SG,en;q=0.9,id;q=0.7",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.185 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.7,ja;q=0.3",
    },
]
