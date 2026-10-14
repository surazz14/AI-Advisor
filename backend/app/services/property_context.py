"""Refresh live property facts (zone, lot area, R-Code, heritage) for a session.

Shared by the WebSocket and REST handlers so both stay in sync.
"""

from __future__ import annotations

import asyncio

from app.services.bushfire_lookup import BushfireStatus, bushfire_status_for_lot
from app.services.heritage_lookup import HeritageInfo, get_heritage
from app.services.lot_lookup import get_lot_parcel, get_lots_by_land_ids
from app.services.rcode_lookup import get_rcode
from app.services.session_store import session_store
from app.services.zone_lookup import (
    ZoneInfo,
    plantagenet_rejection_reason,
    resolve_zone,
)


async def _lot_and_heritage(
    lat: float, lng: float, land_ids: list[int] | None = None
) -> tuple[float | None, int, HeritageInfo | None, BushfireStatus | None]:
    """Lot first (its boundary makes the heritage and bushfire checks accurate).

    With Landgate land_ids (exact address match) we use every lot at that
    address as one site; otherwise we take whichever lot contains the pin.
    Returns (area_m2, lot_count, heritage, bushfire).
    """
    parcel = await get_lots_by_land_ids(land_ids) if land_ids else None
    if parcel is None:
        parcel = await get_lot_parcel(lat, lng)
    rings = parcel.rings if parcel else None
    heritage, bushfire = await asyncio.gather(
        get_heritage(lat, lng, lot_rings=rings),
        # Any part of the lot in the mapped area counts — not just the pin
        asyncio.to_thread(bushfire_status_for_lot, rings, lat, lng),
    )
    if parcel is None:
        return None, 1, heritage, bushfire
    return parcel.area_m2, parcel.lot_count, heritage, bushfire


async def refresh_property_facts(
    session_id: str,
    *,
    address: str | None,
    lat: float | None,
    lng: float | None,
    land_ids: list[int] | None = None,
) -> tuple[ZoneInfo | None, str | None]:
    """Look up zone (every call) plus lot area, R-Code and heritage (once per
    location). Zone, R-Code and the lot→heritage chain run in parallel.

    Returns (zone, rejection_message). rejection_message is set when the pin
    is outside the Shire of Plantagenet (or coords are missing).
    """
    ctx = session_store.get(session_id)
    need_parcel = (
        lat is not None
        and lng is not None
        and ctx is not None
        and not ctx.parcel_checked
    )

    lot_area = None
    lot_count = 1
    rcode = None
    heritage = None
    bushfire = None
    if need_parcel:
        zone, (lot_area, lot_count, heritage, bushfire), rcode = await asyncio.gather(
            resolve_zone(lat=lat, lng=lng, address=address),
            _lot_and_heritage(lat, lng, land_ids),  # type: ignore[arg-type]
            get_rcode(lat, lng),  # type: ignore[arg-type]
        )
    else:
        zone = await resolve_zone(lat=lat, lng=lng, address=address)

    reason = plantagenet_rejection_reason(lat=lat, lng=lng, zone=zone)
    if reason:
        session_store.set_zone(session_id, None)
        return None, reason

    session_store.set_zone(session_id, zone)
    if need_parcel:
        session_store.set_parcel_facts(
            session_id,
            lot_area_m2=lot_area,
            rcode=rcode,
            heritage=heritage,
            lot_count=lot_count,
            bushfire=bushfire,
        )
    return zone, None
