from __future__ import annotations

import asyncio
import logging
import time

from src.core.constants import FINGERPRINTS
from src.core.types import TripleSet
from src.database.apikeys import api_key_manager
from src.database.proxies import proxy_manager

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 5 * 60
BURNED_SECONDS = 30 * 60
POLL_INTERVAL_SECONDS = 2


class TriplePool:
    def __init__(self) -> None:
        self._triples: list[TripleSet] = []
        self._rr_index: int = 0
        self._lock = asyncio.Lock()

    async def refresh(self) -> None:
        async with self._lock:
            await self._refresh_locked()

    async def _refresh_locked(self) -> None:
        active_keys = [item.key for item in api_key_manager.get_all_keys() if item.active]
        active_proxy_urls = [item.proxy for item in proxy_manager.get_all_proxies() if item.active]
        fingerprints = FINGERPRINTS or [{"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}]

        if not active_keys:
            self._triples = []
            return

        if not active_proxy_urls:
            self._triples = []
            logger.error("TriplePool: Tidak ada proxy aktif. Mode Wajib Proxy memblokir proses.")
            return

        previous_state = {
            (triple.api_key, triple.api_url): {
                "in_use": triple.in_use,
                "last_used": triple.last_used,
                "burned": triple.burned,
            }
            for triple in self._triples
        }

        rebuilt: list[TripleSet] = []
        for index, api_key in enumerate(active_keys):
            api_url = active_proxy_urls[index % len(active_proxy_urls)]
            fingerprint = dict(fingerprints[index % len(fingerprints)])
            state = previous_state.get((api_key, api_url), {})
            rebuilt.append(
                TripleSet(
                    api_key=api_key,
                    proxy=api_url,
                    fingerprint=fingerprint,
                    api_url=api_url,
                    in_use=state.get("in_use", False),
                    last_used=state.get("last_used", 0.0),
                    burned=state.get("burned", False),
                )
            )

        self._triples = rebuilt
        if self._rr_index >= len(self._triples):
            self._rr_index = 0

    @staticmethod
    def _is_available(triple: TripleSet, now: float) -> bool:
        if triple.in_use:
            return False
        if triple.last_used <= 0:
            return True

        cooldown = BURNED_SECONDS if triple.burned else COOLDOWN_SECONDS
        return (now - triple.last_used) >= cooldown

    async def acquire(self) -> TripleSet:
        while True:
            async with self._lock:
                if not self._triples:
                    await self._refresh_locked()

                if not self._triples:
                    active_keys = [item.key for item in api_key_manager.get_all_keys() if item.active]
                    if not active_keys:
                        raise RuntimeError("TriplePool kosong: API key tidak tersedia")
                    raise RuntimeError("TriplePool kosong: Proxy tidak tersedia (Fitur generate diwajibkan menggunakan proxy)")

                now = time.time()
                total = len(self._triples)
                for offset in range(total):
                    idx = (self._rr_index + offset) % total
                    triple = self._triples[idx]
                    if not self._is_available(triple, now):
                        continue

                    triple.in_use = True
                    triple.burned = False
                    self._rr_index = (idx + 1) % total
                    
                    if "/change?key=" in triple.api_url:
                        rotated = await proxy_manager.rotate_proxy(triple.api_url)
                        triple.proxy = rotated
                    else:
                        triple.proxy = triple.api_url

                    logger.info(
                        "Triple acquired: key=%s proxy=%s",
                        triple.api_key[:8],
                        "set" if triple.proxy else "direct",
                    )
                    return triple

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def release(self, triple: TripleSet) -> None:
        async with self._lock:
            triple.proxy = triple.api_url
            triple.in_use = False
            triple.burned = False
            triple.last_used = time.time()
            logger.info("Triple released: key=%s", triple.api_key[:8])

    async def mark_burned(self, triple: TripleSet) -> None:
        async with self._lock:
            triple.proxy = triple.api_url
            triple.in_use = False
            triple.burned = True
            triple.last_used = time.time()
            logger.warning("Triple burned: key=%s", triple.api_key[:8])

    def __len__(self) -> int:
        return len(self._triples)
