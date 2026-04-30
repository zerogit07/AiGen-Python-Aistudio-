from __future__ import annotations

import logging

from src.database.client import supabase

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS: dict[str, str] = {
    "bannerImage": "https://picsum.photos/seed/aigen/800/400",
    "bannerDescription": (
        "🔒 *AKSES TERKUNCI*\n\nBot ini bersifat Private/Terbatas.\n\n"
        "Silakan pilih paket:"
    ),
    "paymentImage": "https://picsum.photos/seed/qris/800/800",
    "paymentDescriptionLite": (
        "*AiGen Lite*\n\n- Akses Model Standar\n- Limit: 15 Video/Hari\n"
        "- Harga: Rp99.000/bulan"
    ),
    "paymentDescriptionPro": (
        "*AiGen Pro*\n\n- Akses Model Pro\n- Limit: 50 Video/Hari\n"
        "- Harga: Rp199.000/bulan"
    ),
    "paymentDescriptionUltra": (
        "*AiGen Ultra*\n\n- Akses Semua Model (Ultra + Pro)\n"
        "- Limit: 100 Video/Hari (Unlimited)\n- Harga: Rp299.000/bulan"
    ),
    "limitLite": "15",
    "limitPro": "50",
    "limitUltra": "100",
    "maxLite": "2",
    "maxPro": "3",
    "maxUltra": "5",
    "priceLite": "99000",
    "pricePro": "199000",
    "priceUltra": "299000",
}


class LandingPageManager:
    def __init__(self) -> None:
        self._settings: dict[str, str] = dict(DEFAULT_SETTINGS)

    async def load_settings(self) -> None:
        if not supabase:
            return
        try:
            resp = (
                await supabase.table("settings")
                .select("data")
                .eq("id", "landing")
                .single()
                .execute()
            )
            if resp.data:
                self._settings.update(resp.data.get("data", {}))
                logger.info("Loaded landing settings from Supabase.")
        except Exception as exc:
            logger.error("Error loading landing settings: %s", exc)

    async def set_setting(self, key: str, value: str) -> None:
        self._settings[key] = value
        if supabase:
            try:
                await supabase.table("settings").upsert(
                    {"id": "landing", "data": self._settings}
                ).execute()
            except Exception as exc:
                logger.error("Error saving landing settings: %s", exc)

    def get_setting(self, key: str) -> str:
        return self._settings.get(key, "")


landing_page_manager = LandingPageManager()
