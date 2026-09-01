"""Search Supabase policy_chunks via match_policy_chunks RPC."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client():
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def search_policies(
    query_embedding: list[float],
    *,
    match_count: int = 5,
) -> list[dict]:
    """Return top matching policy rows for the question embedding."""
    result = (
        _client()
        .rpc(
            "match_policy_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "filter_source": None,
                "include_dummy": False,
            },
        )
        .execute()
    )
    rows = list(result.data or [])
    logger.info("RAG retrieve: %s hits", len(rows))
    for i, row in enumerate(rows, start=1):
        sim = row.get("similarity")
        sim_s = f"{float(sim):.3f}" if sim is not None else "?"
        logger.info(
            "  [%s] id=%s source=%s topic=%s similarity=%s",
            i,
            row.get("id"),
            row.get("source_document"),
            row.get("topic"),
            sim_s,
        )
    return rows
