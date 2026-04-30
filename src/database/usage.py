from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.database.client import supabase

logger = logging.getLogger(__name__)


class UsageData:
    def __init__(
        self,
        video_today: int = 0,
        last_reset: str = "",
        video_month: int = 0,
        last_month_reset: str = "",
    ) -> None:
        self.video_today = video_today
        self.last_reset = last_reset
        self.video_month = video_month
        self.last_month_reset = last_month_reset

    def to_dict(self) -> dict:
        return {
            "video_today": self.video_today,
            "last_reset": self.last_reset,
            "video_month": self.video_month,
            "last_month_reset": self.last_month_reset,
        }


class UsageManager:
    def __init__(self) -> None:
        self._usage: dict[str, UsageData] = {}

    async def load_usage(self) -> None:
        if not supabase:
            return
        try:
            resp = await supabase.table("usage").select("*").execute()
            for item in resp.data or []:
                self._usage[str(item["user_id"])] = UsageData(
                    video_today=item.get("video_today", 0),
                    last_reset=item.get("last_reset", ""),
                    video_month=item.get("video_month", 0),
                    last_month_reset=item.get("last_month_reset", ""),
                )
            logger.info("Loaded %d usage records from Supabase.", len(self._usage))
        except Exception as exc:
            logger.error("Error loading usage from Supabase: %s", exc)

    async def get_usage(self, user_id: int) -> UsageData:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        this_month = today[:7]  # YYYY-MM
        id_str = str(user_id)
        data = self._usage.get(id_str)

        if not data:
            data = UsageData(
                video_today=0,
                last_reset=today,
                video_month=0,
                last_month_reset=this_month,
            )
            self._usage[id_str] = data
            if supabase:
                try:
                    await supabase.table("usage").upsert(
                        {"user_id": user_id, **data.to_dict()}
                    ).execute()
                except Exception as exc:
                    logger.error("Error upserting usage: %s %s", user_id, exc)
        else:
            changed = False
            if data.last_reset != today:
                data.video_today = 0
                data.last_reset = today
                changed = True
            if data.last_month_reset != this_month:
                data.video_month = 0
                data.last_month_reset = this_month
                changed = True
            if changed and supabase:
                try:
                    await supabase.table("usage").upsert(
                        {"user_id": user_id, **data.to_dict()}
                    ).execute()
                except Exception as exc:
                    logger.error("Error upserting usage: %s %s", user_id, exc)
        return data

    async def increment_usage(self, user_id: int) -> None:
        data = await self.get_usage(user_id)
        data.video_today += 1
        data.video_month += 1
        if supabase:
            try:
                await supabase.table("usage").upsert(
                    {"user_id": user_id, **data.to_dict()}
                ).execute()
            except Exception as exc:
                logger.error("Error incrementing usage: %s %s", user_id, exc)

    def get_total_usage_today(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return sum(
            d.video_today for d in self._usage.values() if d.last_reset == today
        )

    def get_total_usage_month(self) -> int:
        this_month = datetime.now(timezone.utc).strftime("%Y-%m")
        return sum(
            d.video_month
            for d in self._usage.values()
            if d.last_month_reset == this_month
        )


usage_manager = UsageManager()
