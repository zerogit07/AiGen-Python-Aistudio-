from __future__ import annotations

import asyncio
import logging
import os
import time

from src.core.types import UserState, UserStats
from src.database.users import user_manager

logger = logging.getLogger(__name__)

user_state: dict[int, UserState] = {}

ADMIN_IDS: list[int] = []
_raw = os.getenv("ADMIN_IDS", "")
for part in _raw.split(","):
    part = part.strip()
    if part.isdigit():
        ADMIN_IDS.append(int(part))


def is_user_admin(user_id: int, state: UserState) -> bool:
    return state.is_admin or user_id in ADMIN_IDS


def get_initial_stats() -> UserStats:
    return UserStats()


async def get_or_create_state(
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> UserState:
    await user_manager.add_user(user_id, username, first_name, last_name)
    state = user_state.get(user_id)
    if not state:
        state = UserState(
            api_key_index=0,
            stats=get_initial_stats(),
            current_page=0,
            temp_image_refs=[],
            shots=[],
            current_shot_index=0,
            total_duration=0,
            generate_audio=True,
            use_image=False,
            last_activity=int(time.time() * 1000),
        )
        user_state[user_id] = state
    else:
        state.last_activity = int(time.time() * 1000)
    return state


async def start_state_cleaner() -> None:
    """Background task to clean idle user states every 5 minutes."""
    while True:
        await asyncio.sleep(5 * 60)
        now = int(time.time() * 1000)
        idle_threshold = 30 * 60 * 1000  # 30 minutes
        to_remove = []
        for uid, state in user_state.items():
            if state.is_admin:
                continue
            if now - state.last_activity > idle_threshold:
                to_remove.append(uid)
        for uid in to_remove:
            del user_state[uid]
        if to_remove:
            logger.info("[Auto-Clean] Removed %d idle user states.", len(to_remove))
