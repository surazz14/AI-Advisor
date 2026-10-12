"""Exact address search (Landgate cadastre) used by the frontend autocomplete."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.address_search import search_addresses

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/address", tags=["address"])


@router.get("/search")
async def address_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(8, ge=1, le=20),
) -> dict[str, object]:
    try:
        results = await search_addresses(q, limit=limit)
    except Exception as exc:
        logger.exception("Landgate address search failed q=%r", q[:80])
        # 502 tells the Next.js route to fall back to Nominatim
        raise HTTPException(status_code=502, detail="Address service unavailable") from exc
    return {
        "source": "landgate",
        "attribution": "Address data © Landgate (WA SLIP)",
        "results": results,
    }
