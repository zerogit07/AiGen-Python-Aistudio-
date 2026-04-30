from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.core.types import MemberData
from src.database.client import supabase
from src.database.settings import landing_page_manager

logger = logging.getLogger(__name__)


class MemberManager:
    def __init__(self) -> None:
        self._members: dict[str, MemberData] = {}
        self._in_progress_count: dict[str, int] = {}
        self._custom_limits: dict[str, dict[str, int]] = {}

    async def load_members(self) -> None:
        if not supabase:
            return
        try:
            resp = supabase.table("members").select("*").execute()
            for row in resp.data or []:
                id_str = str(row["user_id"])
                self._members[id_str] = MemberData(
                    plan=row.get("plan", "testing"),
                    expire_date=row.get("expired"),
                    testing_quota=row.get("testing_quota", 0),
                    active=row.get("active", True),
                    current_process=row.get("current_process", 0),
                )
            logger.info("Loaded %d members from Supabase.", len(self._members))
        except Exception as exc:
            logger.error("Error loading members: %s", exc)

    async def load_custom_limits(self) -> None:
        if not supabase:
            return
        try:
            resp = (
                supabase.table("settings")
                .select("id, data")
                .eq("id", "custom_limits")
                .execute()
            )
            if resp.data and resp.data[0].get("data"):
                limits_data = resp.data[0]["data"]
                for user_id, limits in limits_data.items():
                    if isinstance(limits, dict):
                        self._custom_limits[user_id] = {}
                        for limit_type, val in limits.items():
                            try:
                                self._custom_limits[user_id][limit_type] = int(val)
                            except (ValueError, TypeError):
                                pass
            logger.info(
                "Loaded custom limits for %d users.", len(self._custom_limits)
            )
        except Exception as exc:
            logger.error("Error loading custom limits: %s", exc)

    async def sync_member(self, user_id: int | str) -> MemberData | None:
        id_str = str(user_id)
        if supabase:
            try:
                resp = (
                    supabase.table("members")
                    .select("*")
                    .eq("user_id", id_str)
                    .single()
                    .execute()
                )
                if resp.data:
                    existing = self._members.get(id_str)
                    new_data = MemberData(
                        plan=resp.data.get("plan", existing.plan if existing else "testing"),
                        expire_date=resp.data.get("expired", existing.expire_date if existing else None),
                        testing_quota=resp.data.get("testing_quota", existing.testing_quota if existing else 0),
                        active=resp.data.get("active", existing.active if existing else True),
                        current_process=resp.data.get("current_process", existing.current_process if existing else 0),
                    )
                    self._members[id_str] = new_data
            except Exception as exc:
                logger.error("Error syncing member %s: %s", id_str, exc)
        return self.get_member_data(user_id)

    async def count_active_processes(self, user_id: int | str) -> int:
        if supabase:
            try:
                resp = (
                    supabase.table("jobs")
                    .select("*", count="exact")
                    .eq("user_id", str(user_id))
                    .eq("status", "processing")
                    .execute()
                )
                if resp.count is not None:
                    return resp.count
            except Exception:
                pass
        return self._in_progress_count.get(str(user_id), 0)

    def get_member_data(self, user_id: int | str) -> MemberData | None:
        id_str = str(user_id)
        data = self._members.get(id_str)
        if not data:
            return None

        now = datetime.now(timezone.utc)
        if data.expire_date:
            try:
                expire_date = datetime.fromisoformat(data.expire_date.replace("Z", "+00:00"))
            except ValueError:
                expire_date = None
        else:
            expire_date = None

        is_expired = (now > expire_date) if expire_date is not None else False
        diff = abs((expire_date - now).days) if expire_date is not None else 0

        data.is_expired = is_expired
        data.remaining_days = diff
        data.is_member = True
        return data

    def get_daily_limit(self, plan: str, user_id: int | str | None = None) -> int:
        if user_id:
            id_str = str(user_id)
            custom = self._custom_limits.get(id_str, {}).get("daily")
            if custom:
                return custom
        if plan == "ultra":
            return int(landing_page_manager.get_setting("limitUltra") or "999")
        if plan == "pro":
            return int(landing_page_manager.get_setting("limitPro") or "50")
        if plan == "lite":
            return int(landing_page_manager.get_setting("limitLite") or "20")
        return 3  # free trial

    def get_max_process(self, plan: str, user_id: int | str | None = None) -> int:
        if user_id:
            id_str = str(user_id)
            custom = self._custom_limits.get(id_str, {}).get("max")
            if custom:
                return custom
        if plan == "ultra":
            return int(landing_page_manager.get_setting("maxUltra") or "5")
        if plan == "pro":
            return int(landing_page_manager.get_setting("maxPro") or "3")
        if plan == "lite":
            return int(landing_page_manager.get_setting("maxLite") or "2")
        return 1

    async def reset_process(self, user_id: int | str) -> None:
        id_str = str(user_id)
        self._in_progress_count[id_str] = 0
        if supabase:
            try:
                supabase.table("members").update({"current_process": 0}).eq(
                    "user_id", id_str
                ).execute()
            except Exception:
                pass

    async def start_process(self, user_id: int | str, plan: str) -> bool:
        id_str = str(user_id)
        current = self._in_progress_count.get(id_str, 0)
        max_proc = self.get_max_process(plan, user_id)
        if current >= max_proc:
            return False
        self._in_progress_count[id_str] = current + 1
        if supabase:
            try:
                supabase.table("members").update(
                    {"current_process": current + 1}
                ).eq("user_id", id_str).execute()
            except Exception:
                pass
        return True

    async def end_process(self, user_id: int | str) -> None:
        id_str = str(user_id)
        current = self._in_progress_count.get(id_str, 0)
        self._in_progress_count[id_str] = max(0, current - 1)
        if supabase:
            try:
                supabase.table("members").update(
                    {"current_process": max(0, current - 1)}
                ).eq("user_id", id_str).execute()
            except Exception:
                pass

    async def add_member(
        self,
        user_id: int | str,
        plan: str,
        days: int = 30,
        testing_quota: int = 3,
    ) -> None:
        id_str = str(user_id)
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        expire = now + timedelta(days=days)
        member = MemberData(
            plan=plan,
            expire_date=expire.isoformat(),
            testing_quota=testing_quota,
            active=True,
            current_process=0,
        )
        self._members[id_str] = member
        if supabase:
            try:
                supabase.table("members").upsert(
                    {
                        "user_id": id_str,
                        "plan": plan,
                        "expired": expire.isoformat(),
                        "testing_quota": testing_quota,
                        "active": True,
                        "current_process": 0,
                    }
                ).execute()
            except Exception as exc:
                logger.error("Error adding member: %s %s", id_str, exc)

    async def remove_member(self, user_id: int | str) -> None:
        id_str = str(user_id)
        self._members.pop(id_str, None)
        if supabase:
            try:
                supabase.table("members").delete().eq("user_id", id_str).execute()
            except Exception:
                pass

    def get_all_members(self) -> dict[str, MemberData]:
        return self._members

    def get_members_by_plan(self, plan: str) -> list[str]:
        return [
            uid for uid, m in self._members.items() if m.plan == plan
        ]


member_manager = MemberManager()
