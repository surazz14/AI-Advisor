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
    client = _client()
    result = (
        client.rpc(
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

    # Enrich with section/page fields stored in the table (for correct citations)
    ids = [str(r.get("id")) for r in rows if r.get("id")]
    if ids:
        detail = (
            client.table("policy_chunks")
            .select(
                "id,section,subsection,page,topic,item_ref,source_document,document,clause_type"
            )
            .in_("id", ids)
            .execute()
        )
        by_id = {str(r["id"]): r for r in (detail.data or [])}
        enriched: list[dict] = []
        for row in rows:
            rid = str(row.get("id"))
            extra = by_id.get(rid, {})
            merged = {**row, **extra}
            enriched.append(merged)
        rows = enriched

    logger.info("RAG retrieve: %s hits", len(rows))
    for i, row in enumerate(rows, start=1):
        sim = row.get("similarity")
        sim_s = f"{float(sim):.3f}" if sim is not None else "?"
        logger.info(
            "  [%s] id=%s source=%s section=%s page=%s similarity=%s",
            i,
            row.get("id"),
            row.get("source_document"),
            row.get("section"),
            row.get("page"),
            sim_s,
        )
    return rows
