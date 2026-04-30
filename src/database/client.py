from __future__ import annotations

import logging
import os
import asyncio

from supabase import create_client, Client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_sync_supabase: Client | None = None

class AsyncSupabaseQueryBuilder:
    def __init__(self, builder):
        self.builder = builder

    def __getattr__(self, name):
        attr = getattr(self.builder, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                return AsyncSupabaseQueryBuilder(attr(*args, **kwargs))
            return wrapper
        return attr

    async def execute(self):
        return await asyncio.to_thread(self.builder.execute)

class AsyncSupabaseClient:
    def __init__(self, client):
        self.client = client

    def table(self, table_name: str):
        return AsyncSupabaseQueryBuilder(self.client.table(table_name))
        
    @property
    def auth(self):
        return self.client.auth

supabase: AsyncSupabaseClient | None = None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        _sync_supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        supabase = AsyncSupabaseClient(_sync_supabase)
        logger.info("Async Supabase client wrapper initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize Supabase client: %s", exc)
else:
    logger.warning(
        "Supabase credentials (SUPABASE_URL / SUPABASE_ANON_KEY) are missing. "
        "Database features will be unavailable."
    )
