from __future__ import annotations

import logging

from src.core.constants import DEFAULT_MODELS
from src.database.client import supabase

logger = logging.getLogger(__name__)


class ModelStatus:
    def __init__(self, model_id: str, active: bool = True) -> None:
        self.id = model_id
        self.active = active


class ModelManager:
    def __init__(self) -> None:
        self._status: list[ModelStatus] = []
        self._maintenance_mode: bool = False

    async def load_status(self) -> None:
        if not supabase:
            return
        try:
            # Load maintenance mode
            try:
                resp = (
                    supabase.table("settings")
                    .select("id, data")
                    .eq("id", "maintenance")
                    .execute()
                )
                if resp.data and len(resp.data) > 0:
                    self._maintenance_mode = resp.data[0].get("data", {}).get("active", False)
            except Exception:
                pass

            resp = supabase.table("models_status").select("*").execute()
            self._status = [
                ModelStatus(model_id=item["id"], active=item.get("active", True))
                for item in (resp.data or [])
            ]

            # Initialize missing models
            for dm in DEFAULT_MODELS:
                if not any(s.id == dm["id"] for s in self._status):
                    new_status = ModelStatus(model_id=dm["id"], active=True)
                    self._status.append(new_status)
                    try:
                        supabase.table("models_status").upsert(
                            {"id": dm["id"], "active": True}
                        ).execute()
                    except Exception:
                        pass

            logger.info("Loaded %d models status from Supabase.", len(self._status))
        except Exception as exc:
            logger.error("Error loading models status: %s", exc)

    async def toggle_model(self, model_id_or_name: str) -> bool:
        entry = next((s for s in self._status if s.id == model_id_or_name), None)
        if not entry:
            model_by_name = next(
                (
                    m
                    for m in DEFAULT_MODELS
                    if model_id_or_name.lower() in m["name"].lower()
                ),
                None,
            )
            if model_by_name:
                entry = next(
                    (s for s in self._status if s.id == model_by_name["id"]), None
                )

        if entry:
            entry.active = not entry.active
            if supabase:
                try:
                    supabase.table("models_status").update(
                        {"active": entry.active}
                    ).eq("id", entry.id).execute()
                except Exception as exc:
                    logger.error("Error toggling model: %s %s", entry.id, exc)
            return True
        return False

    async def toggle_maintenance(self) -> bool:
        self._maintenance_mode = not self._maintenance_mode
        if supabase:
            try:
                supabase.table("settings").upsert(
                    {"id": "maintenance", "data": {"active": self._maintenance_mode}}
                ).execute()
            except Exception as exc:
                logger.error("Error toggling maintenance: %s", exc)
        return self._maintenance_mode

    def is_maintenance(self) -> bool:
        return self._maintenance_mode

    def get_all_models_with_status(self) -> list[dict]:
        result = []
        for dm in DEFAULT_MODELS:
            s = next((st for st in self._status if st.id == dm["id"]), None)
            result.append({**dm, "active": s.active if s else True})
        return result

    def get_active_models(self) -> list[dict]:
        return [
            dm
            for dm in DEFAULT_MODELS
            if next(
                (s for s in self._status if s.id == dm["id"]),
                ModelStatus(dm["id"], True),
            ).active
        ]


model_manager = ModelManager()
