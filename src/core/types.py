from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApiKey:
    key: str
    active: bool = True
    cooldown_until: int = 0  # timestamp in ms


@dataclass
class ProxyEntry:
    proxy: str
    active: bool = True
    cooldown_until: int = 0  # timestamp in ms


@dataclass
class TripleSet:
    api_key: str
    proxy: str
    fingerprint: dict
    in_use: bool = False
    last_used: float = 0.0
    burned: bool = False


@dataclass
class MemberData:
    plan: str  # "lite" | "pro" | "ultra" | "testing"
    start_date: Optional[str] = None
    expire_date: Optional[str] = None
    expired: Optional[str] = None
    quota_used: int = 0
    testing_quota: int = 0
    active: bool = True
    current_process: int = 0
    is_expired: bool = False
    remaining_days: int = 0
    is_member: bool = True


@dataclass
class Shot:
    prompt: str = ""
    duration: int = 5


@dataclass
class UserStats:
    total_videos: int = 0
    model_usage: dict[str, int] = field(default_factory=dict)


@dataclass
class UserState:
    model: Optional[str] = None
    mode: Optional[str] = None  # "interpolation" | "reference"
    kling3_mode: Optional[str] = None  # "single" | "multi_intelligence" | "multi_customize"
    duration: Optional[str] = None
    aspect_ratio: Optional[str] = None
    orientation: Optional[str] = None  # "video" | "image"
    generate_audio: bool = True
    use_image: bool = False
    resolution: Optional[str] = None  # "720" | "1080" | "4k" | "1k" | "2k"
    step: Optional[str] = None
    temp_image_url: Optional[str] = None
    temp_image_url_last: Optional[str] = None
    temp_image_refs: list[str] = field(default_factory=list)
    temp_video_url: Optional[str] = None
    temp_prompt: Optional[str] = None
    shots: list[Shot] = field(default_factory=list)
    current_shot_index: int = 0
    total_duration: int = 0
    api_key_index: int = 0
    awaiting_api_key: bool = False
    waiting_proxy: bool = False
    waiting_add_member: bool = False
    waiting_broadcast: bool = False
    broadcast_target: Optional[str] = None  # "all" | "member" | "trial"
    waiting_payment_proof: bool = False
    waiting_welcome_banner: bool = False
    waiting_welcome_headline: bool = False
    waiting_welcome_desc: bool = False
    waiting_pro_price: bool = False
    waiting_ultra_price: bool = False
    waiting_free_trial_price: bool = False
    waiting_qris_url: bool = False
    waiting_lp_banner_img: bool = False
    waiting_lp_banner_desc: bool = False
    waiting_lp_pay_img: bool = False
    waiting_lp_pay_desc_lite: bool = False
    waiting_lp_pay_desc_pro: bool = False
    waiting_lp_pay_desc_ultra: bool = False
    waiting_lp_limit_lite: bool = False
    waiting_lp_limit_pro: bool = False
    waiting_lp_limit_ultra: bool = False
    waiting_lp_price_lite: bool = False
    waiting_lp_price_pro: bool = False
    waiting_lp_price_ultra: bool = False
    temp_unique_code: int = 0
    temp_plan: Optional[str] = None  # "lite" | "pro" | "ultra"
    is_admin: bool = False
    stats: UserStats = field(default_factory=UserStats)
    current_page: int = 0
    is_admin_panel: bool = False
    last_activity: int = 0
    waiting_chat_id: bool = False
    chatting_with: Optional[int] = None
    waiting_check_user: bool = False
    multi_shot_on: bool = False
    panel_view: Optional[str] = None
    camera_config: Optional[dict] = None


@dataclass
class ModelStats:
    total_videos: int = 0
    model_usage: dict[str, int] = field(default_factory=dict)
