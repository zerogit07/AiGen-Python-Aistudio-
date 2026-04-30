from __future__ import annotations

import logging
import time

import httpx

from src.core.types import TripleSet
from src.database.apikeys import api_key_manager
from src.database.proxies import proxy_manager

logger = logging.getLogger(__name__)


class RequestEngineHTTPError(RuntimeError):
    def __init__(self, status_code: int, detail: str = "") -> None:
        self.status_code = status_code
        self.detail = detail
        message = f"{status_code} - {detail}" if detail else str(status_code)
        super().__init__(message)


async def _request_once(
    method: str,
    url: str,
    api_key: str,
    proxy_url: str | None,
    headers: dict | None,
    json_data: dict | None,
    fingerprint: dict | None = None,
) -> dict:
    req_headers = dict(headers or {})
    if fingerprint:
        req_headers.update(fingerprint)
    req_headers["x-freepik-api-key"] = api_key
    req_headers.setdefault("Content-Type", "application/json")

    logger.info(
        "[Request] Key %s... %s",
        api_key[:8],
        "via Proxy" if proxy_url else "Direct",
    )

    async with httpx.AsyncClient(timeout=15, proxy=proxy_url) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=req_headers,
            json=json_data,
        )
        response.raise_for_status()
        return {"data": response.json(), "used_key": api_key}


async def request_engine(
    method: str,
    url: str,
    headers: dict | None = None,
    json_data: dict | None = None,
    force_api_key: str | None = None,
    triple_set: TripleSet | None = None,
) -> dict:
    """Resilient request wrapper with API key rotation and proxy support."""
    if triple_set is not None:
        try:
            return await _request_once(
                method=method,
                url=url,
                api_key=triple_set.api_key,
                proxy_url=triple_set.proxy or None,
                headers=headers,
                json_data=json_data,
                fingerprint=triple_set.fingerprint,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = exc.response.text
            if status in (403, 429):
                raise RequestEngineHTTPError(status, detail) from exc
            if status == 400:
                raise RuntimeError(f"{status} - {detail}") from exc
            if status == 401:
                await api_key_manager.mark_key_dead(triple_set.api_key)
            raise RuntimeError(f"{status} - {detail}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"500 - {exc}") from exc

    last_error: Exception | None = None
    now = int(time.time() * 1000)

    keys_to_try = []

    if force_api_key:
        forced = next(
            (
                k
                for k in api_key_manager.get_all_keys()
                if k.key == force_api_key and k.active and k.cooldown_until < now
            ),
            None,
        )
        if forced:
            keys_to_try.append(forced)

    rotated = api_key_manager.get_rotated_keys()
    for api_key_obj in rotated:
        if not any(existing.key == api_key_obj.key for existing in keys_to_try):
            keys_to_try.append(api_key_obj)

    if not keys_to_try and force_api_key:
        forced = next(
            (
                k
                for k in api_key_manager.get_all_keys()
                if k.key == force_api_key and k.active
            ),
            None,
        )
        if forced:
            keys_to_try.append(forced)

    if not keys_to_try:
        raise RuntimeError("Semua API Key sedang sibuk atau tidak tersedia")

    for api_key_obj in keys_to_try:
        api_key = api_key_obj.key
        skip_to_next_key = False

        max_proxy_try = 3
        for _ in range(max_proxy_try):
            proxy_url = proxy_manager.get_rotated_proxy_url()
            try:
                result = await _request_once(
                    method=method,
                    url=url,
                    api_key=api_key,
                    proxy_url=proxy_url,
                    headers=headers,
                    json_data=json_data,
                )
                if not force_api_key:
                    api_key_manager.update_index()
                return result

            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                detail = exc.response.text

                if status == 400:
                    raise RuntimeError(f"{status} - {detail}") from exc

                if status in (403, 429):
                    raise RequestEngineHTTPError(status, detail) from exc

                if status == 401:
                    logger.error(
                        "[Unauthorized] Key %s invalid (401). Disabling.",
                        api_key[:8],
                    )
                    await api_key_manager.mark_key_dead(api_key)
                    skip_to_next_key = True
                    break

                if status == 500:
                    logger.error("[Server Error] 500 from API with key %s", api_key[:8])
                    if proxy_url:
                        await proxy_manager.set_cooldown(proxy_url)
                    continue

                if status == 503:
                    logger.warning(
                        "[Service Unavailable] 503 from API with key %s",
                        api_key[:8],
                    )
                    if proxy_url:
                        await proxy_manager.set_cooldown(proxy_url)
                    continue

                logger.warning(
                    "[Unexpected] Status %d from API with key %s",
                    status,
                    api_key[:8],
                )
                if proxy_url:
                    await proxy_manager.set_cooldown(proxy_url)

            except Exception as exc:
                last_error = exc
                if proxy_url:
                    await proxy_manager.set_cooldown(proxy_url)

        if skip_to_next_key:
            continue

        try:
            result = await _request_once(
                method=method,
                url=url,
                api_key=api_key,
                proxy_url=None,
                headers=headers,
                json_data=json_data,
            )
            if not force_api_key:
                api_key_manager.update_index()
            return result

        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code
            detail = exc.response.text
            if status == 400:
                raise RuntimeError(f"{status} - {detail}") from exc
            if status in (403, 429):
                raise RequestEngineHTTPError(status, detail) from exc
            if status == 401:
                await api_key_manager.mark_key_dead(api_key)
                continue
        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(f"500 - Semua request gagal: {last_error}") from last_error
    raise RuntimeError("500 - Semua request gagal")
