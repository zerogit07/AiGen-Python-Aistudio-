from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.database.client import supabase

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self) -> None:
        self._users: set[str] = set()

    async def load_users(self) -> None:
        if not supabase:
            return
        try:
            resp = supabase.table("users").select("id").execute()
            for row in resp.data or []:
                if row.get("id"):
                    self._users.add(str(row["id"]))
            logger.info("Loaded %d users from Supabase.", len(self._users))
        except Exception as exc:
            logger.error("Error loading users from Supabase: %s", exc)

    async def add_user(
        self,
        user_id: int | str,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        id_str = str(user_id)
        full_name = " ".join(filter(None, [first_name, last_name])) or None
        if id_str not in self._users:
            self._users.add(id_str)
            if supabase:
                try:
                    supabase.table("users").upsert(
                        {
                            "id": int(id_str),
                            "username": username or "",
                            "first_name": first_name or "",
                            "last_name": last_name or "",
                            "joined_at": datetime.now(timezone.utc).isoformat(),
                        },
                        on_conflict="id",
                    ).execute()
                    logger.info("Saved new user %s to Supabase", id_str)
                except Exception as exc:
                    logger.error("Error saving user %s to Supabase: %s", id_str, exc)

    async def get_user_data(self, user_id: int | str) -> dict | None:
        if not supabase:
            return None
        try:
            resp = (
                supabase.table("users")
                .select("*")
                .eq("id", int(str(user_id)))
                .single()
                .execute()
            )
            return resp.data
        except Exception:
            return None

    def get_all_users(self) -> list[str]:
        return list(self._users)


user_manager = UserManager()
