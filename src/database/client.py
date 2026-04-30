from __future__ import annotations

import logging
import os

from supabase import create_client, Client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

supabase: Client | None = None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize Supabase client: %s", exc)
else:
    logger.warning(
        "Supabase credentials (SUPABASE_URL / SUPABASE_ANON_KEY) are missing. "
        "Database features will be unavailable."
    )
