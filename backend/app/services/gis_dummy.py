"""Deprecated shim — dummy GIS removed.

Use ``app.services.zone_lookup`` (live SLIP zone API) instead.
"""

from __future__ import annotations

from app.services.zone_lookup import ZoneInfo, get_zone_info, resolve_zone

__all__ = ["ZoneInfo", "get_zone_info", "resolve_zone", "lookup_zone"]


def lookup_zone(
    *,
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> ZoneInfo | None:
    """Sync stub kept for old imports — always returns None.

    Live zoning is async: ``await resolve_zone(lat=..., lng=..., address=...)``.
    """
    _ = (address, lat, lng)
    return None
