from __future__ import annotations

import logging
import time

import httpx

from src.core.types import ProxyEntry
from src.database.client import supabase

logger = logging.getLogger(__name__)


class ProxyManager:
    def __init__(self) -> None:
        self._proxies: list[ProxyEntry] = []
        self._current_index: int = 0

    async def load_proxies(self) -> None:
        if not supabase:
            return
        try:
            resp = supabase.table("proxies").select("*").execute()
            self._proxies = [
                ProxyEntry(
                    proxy=item["proxy"],
                    active=item.get("active", True),
                    cooldown_until=int(item.get("cooldown_until", 0)),
                )
                for item in (resp.data or [])
            ]
            logger.info("Loaded %d proxies from Supabase.", len(self._proxies))
        except Exception as exc:
            logger.error("Error loading proxies: %s", exc)

    async def add_proxy(self, proxy: str) -> None:
        if not any(p.proxy == proxy for p in self._proxies):
            new_proxy = ProxyEntry(proxy=proxy, active=True, cooldown_until=0)
            self._proxies.append(new_proxy)
            if supabase:
                try:
                    supabase.table("proxies").upsert(
                        {"proxy": proxy, "active": True, "cooldown_until": 0}
                    ).execute()
                except Exception as exc:
                    logger.error("Error adding proxy: %s %s", proxy, exc)

    async def remove_proxy(self, proxy: str) -> None:
        self._proxies = [p for p in self._proxies if p.proxy != proxy]
        if supabase:
            try:
                supabase.table("proxies").delete().eq("proxy", proxy).execute()
            except Exception as exc:
                logger.error("Error removing proxy: %s %s", proxy, exc)

    async def toggle_proxy(self, proxy: str) -> bool:
        entry = next((p for p in self._proxies if p.proxy == proxy), None)
        if entry:
            entry.active = not entry.active
            if supabase:
                try:
                    supabase.table("proxies").update({"active": entry.active}).eq(
                        "proxy", proxy
                    ).execute()
                except Exception as exc:
                    logger.error("Error toggling proxy: %s %s", proxy, exc)
            return True
        return False

    async def enable_all(self) -> None:
        for p in self._proxies:
            p.active = True
            p.cooldown_until = 0
        if supabase:
            try:
                supabase.table("proxies").update(
                    {"active": True, "cooldown_until": 0}
                ).neq("proxy", "").execute()
            except Exception:
                pass

    async def disable_all(self) -> None:
        for p in self._proxies:
            p.active = False
        if supabase:
            try:
                supabase.table("proxies").update({"active": False}).neq(
                    "proxy", ""
                ).execute()
            except Exception:
                pass

    async def delete_all(self) -> None:
        self._proxies = []
        if supabase:
            try:
                supabase.table("proxies").delete().neq("proxy", "").execute()
            except Exception:
                pass

    async def check_all_proxies(self) -> dict[str, int]:
        active_count = 0
        dead_count = 0
        async with httpx.AsyncClient(timeout=5) as client:
            for p in self._proxies:
                try:
                    await client.get(
                        "http://www.google.com",
                        proxy=p.proxy,
                    )
                    p.active = True
                    p.cooldown_until = 0
                    active_count += 1
                except Exception:
                    p.active = False
                    dead_count += 1
                if supabase:
                    try:
                        supabase.table("proxies").update(
                            {"active": p.active, "cooldown_until": p.cooldown_until}
                        ).eq("proxy", p.proxy).execute()
                    except Exception:
                        pass
        return {
            "total": len(self._proxies),
            "active_count": active_count,
            "dead_count": dead_count,
        }

    def get_all_proxies(self) -> list[ProxyEntry]:
        return self._proxies

    async def rotate_proxy(self, api_url: str) -> str:
        if "/change?key=" in api_url:
            from src.core.constants import PROXY_ROTATION_TIMEOUT
            try:
                async with httpx.AsyncClient(timeout=PROXY_ROTATION_TIMEOUT) as client:
                    resp = await client.get(api_url)
                    resp.raise_for_status()
                    text = resp.text.strip()
                    if text:
                        if not text.startswith("http"):
                            return f"http://{text}"
                        return text
                    else:
                        logger.error("Empty response from proxy rotation API")
                        return api_url
            except Exception as e:
                logger.error("Failed to rotate proxy via API %s: %s", api_url, e)
                return api_url
        return api_url

    def get_rotated_proxy_url(self) -> str | None:
        now = int(time.time() * 1000)
        available = [p for p in self._proxies if p.active and p.cooldown_until < now]
        if not available:
            return None
        proxy = available[self._current_index % len(available)]
        self._current_index = (self._current_index + 1) % len(available)
        return proxy.proxy

    async def set_cooldown(self, proxy_url: str) -> None:
        if not proxy_url:
            return
        entry = next(
            (p for p in self._proxies if proxy_url in p.proxy or p.proxy in proxy_url),
            None,
        )
        if entry:
            duration = 15 * 60 * 1000  # 15 mins
            entry.cooldown_until = int(time.time() * 1000) + duration
            logger.info("[Cooldown Proxy] set for 15 mins")
            if supabase:
                try:
                    supabase.table("proxies").update(
                        {"cooldown_until": entry.cooldown_until}
                    ).eq("proxy", entry.proxy).execute()
                except Exception:
                    pass

    def has_proxies(self) -> bool:
        return any(p.active for p in self._proxies)


proxy_manager = ProxyManager()
