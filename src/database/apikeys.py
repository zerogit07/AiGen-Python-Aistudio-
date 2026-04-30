from __future__ import annotations

import logging
import random
import time

import httpx

from src.core.types import ApiKey
from src.database.client import supabase

logger = logging.getLogger(__name__)


class ApiKeyManager:
    def __init__(self) -> None:
        self._keys: list[ApiKey] = []
        self._current_index: int = 0

    async def load_keys(self) -> None:
        if not supabase:
            return
        try:
            resp = supabase.table("api_keys").select("*").execute()
            self._keys = [
                ApiKey(
                    key=item["key"],
                    active=item.get("active", True),
                    cooldown_until=int(item.get("cooldown_until", 0)),
                )
                for item in (resp.data or [])
            ]
            logger.info("Loaded %d Freepik API keys from Supabase.", len(self._keys))
        except Exception as exc:
            logger.error("Error loading keys from Supabase: %s", exc)

    def get_all_keys(self) -> list[ApiKey]:
        return self._keys

    def get_shuffled_active_keys(self) -> list[str]:
        now = int(time.time() * 1000)
        active = [k.key for k in self._keys if k.active and k.cooldown_until < now]
        random.shuffle(active)
        return active

    def get_rotated_keys(self) -> list[ApiKey]:
        now = int(time.time() * 1000)
        available = [k for k in self._keys if k.active and k.cooldown_until < now]
        if not available:
            return []
        sorted_keys = list(self._keys)
        rotated: list[ApiKey] = []
        for i in range(len(sorted_keys)):
            idx = (self._current_index + i) % len(sorted_keys)
            k = sorted_keys[idx]
            if k.active and k.cooldown_until < now:
                rotated.append(k)
        return rotated

    def update_index(self) -> None:
        if self._keys:
            self._current_index = (self._current_index + 1) % len(self._keys)

    async def set_cooldown(self, key: str, custom_duration_seconds: int | None = None) -> None:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            duration = (
                custom_duration_seconds * 1000
                if custom_duration_seconds
                else random.randint(60, 120) * 1000
            )
            ak.cooldown_until = int(time.time() * 1000) + duration
            logger.info("[Cooldown] Key %s... set for %ds", key[:8], duration // 1000)
            if supabase:
                try:
                    supabase.table("api_keys").update(
                        {"cooldown_until": ak.cooldown_until}
                    ).eq("key", key).execute()
                except Exception:
                    pass

    async def mark_key_dead(self, key: str) -> None:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            ak.active = False
            if supabase:
                try:
                    supabase.table("api_keys").update({"active": False}).eq(
                        "key", key
                    ).execute()
                except Exception as exc:
                    logger.error("Error marking key dead in Supabase: %s %s", key, exc)

    async def add_key(self, key: str) -> None:
        if not any(ak.key == key for ak in self._keys):
            new_key = ApiKey(key=key, active=True, cooldown_until=0)
            self._keys.append(new_key)
            if supabase:
                try:
                    supabase.table("api_keys").upsert(
                        {"key": key, "active": True, "cooldown_until": 0}
                    ).execute()
                except Exception as exc:
                    logger.error("Error adding key to Supabase: %s %s", key, exc)

    async def remove_key(self, key: str) -> None:
        self._keys = [ak for ak in self._keys if ak.key != key]
        if supabase:
            try:
                supabase.table("api_keys").delete().eq("key", key).execute()
            except Exception as exc:
                logger.error("Error removing key from Supabase: %s %s", key, exc)

    async def toggle_key(self, key: str) -> bool:
        ak = next((k for k in self._keys if k.key == key), None)
        if ak:
            ak.active = not ak.active
            if supabase:
                try:
                    supabase.table("api_keys").update({"active": ak.active}).eq(
                        "key", key
                    ).execute()
                except Exception as exc:
                    logger.error("Error toggling key in Supabase: %s %s", key, exc)
            return True
        return False

    async def enable_all(self) -> None:
        for k in self._keys:
            k.active = True
            k.cooldown_until = 0
        if supabase:
            try:
                supabase.table("api_keys").update(
                    {"active": True, "cooldown_until": 0}
                ).neq("key", "").execute()
            except Exception as exc:
                logger.error("Error enabling all keys: %s", exc)

    async def disable_all(self) -> None:
        for k in self._keys:
            k.active = False
        if supabase:
            try:
                supabase.table("api_keys").update({"active": False}).neq("key", "").execute()
            except Exception as exc:
                logger.error("Error disabling all keys: %s", exc)

    async def delete_all(self) -> None:
        self._keys = []
        if supabase:
            try:
                supabase.table("api_keys").delete().neq("key", "").execute()
            except Exception as exc:
                logger.error("Error deleting all keys: %s", exc)

    async def test_all_keys(self) -> dict[str, int]:
        valid = 0
        limit = 0
        invalid = 0
        total = len(self._keys)

        if total == 0:
            return {"valid": valid, "limit": limit, "invalid": invalid, "total": total}

        async with httpx.AsyncClient(timeout=10) as client:
            for k in self._keys:
                try:
                    resp = await client.get(
                        "https://api.freepik.com/v1/ai/text-to-image/nano-banana-pro",
                        headers={"x-freepik-api-key": k.key},
                    )
                    if resp.status_code in (404, 400, 405):
                        valid += 1
                        if not k.active or k.cooldown_until > int(time.time() * 1000):
                            k.active = True
                            k.cooldown_until = 0
                            if supabase:
                                try:
                                    supabase.table("api_keys").update(
                                        {"active": True, "cooldown_until": 0}
                                    ).eq("key", k.key).execute()
                                except Exception:
                                    pass
                    elif resp.status_code == 200:
                        valid += 1
                        if not k.active:
                            k.active = True
                            k.cooldown_until = 0
                            if supabase:
                                try:
                                    supabase.table("api_keys").update(
                                        {"active": True, "cooldown_until": 0}
                                    ).eq("key", k.key).execute()
                                except Exception:
                                    pass
                    elif resp.status_code == 429:
                        limit += 1
                    else:
                        invalid += 1
                        await self.mark_key_dead(k.key)
                except Exception:
                    invalid += 1

        return {"valid": valid, "limit": limit, "invalid": invalid, "total": total}


api_key_manager = ApiKeyManager()
