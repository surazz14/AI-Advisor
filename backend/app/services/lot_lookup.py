"""Lot / site area from Landgate cadastre via WA SLIP.

Layer: "Cadastre (No Attributes) (LGATE-001)"
https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/Property_and_Planning/MapServer/2

The layer has no area attribute, so we request the parcel polygon that
contains the pin, projected to GDA2020 / MGA zone 50 (metres), and compute
its area with the shoelace formula.

The pin comes from address geocoding, so it can land on a road reserve or a
neighbouring lot. Treat the result as approximate and say so to the user.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_CADASTRE_QUERY_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/Property_and_Planning/MapServer/2/query"
)

# GDA2020 / MGA zone 50 (metres) — covers the Shire of Plantagenet (114°E–120°E)
MGA_ZONE_50 = 7850
_TIMEOUT_SECONDS = 6.0


def ring_signed_area(ring: list[list[float]]) -> float:
    """Shoelace signed area of one ring (counter-clockwise = positive)."""
    if len(ring) < 3:
        return 0.0
    points = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    return (
        sum(
            x1 * y2 - x2 * y1
            for (x1, y1, *_), (x2, y2, *_) in zip(points, points[1:])
        )
        / 2.0
    )


def polygon_area(rings: list[list[list[float]]]) -> float:
    """Area of an Esri polygon in the units² of its coordinates.

    Esri outer rings are clockwise and holes counter-clockwise, so summing the
    signed areas and flipping the sign subtracts holes correctly.
    """
    return abs(-sum(ring_signed_area(r) for r in rings))


def format_lot_area(area_m2: float | None) -> str | None:
    """Human label like '3,235 m² (≈0.32 ha)'."""
    if area_m2 is None or area_m2 <= 0:
        return None
    hectares = area_m2 / 10_000
    if area_m2 >= 10_000:
        return f"{hectares:,.2f} ha ({area_m2:,.0f} m²)"
    return f"{area_m2:,.0f} m² (≈{hectares:.2f} ha)"


@dataclass
class LotParcel:
    """Cadastral lot at the pin, in GDA2020 / MGA zone 50 metres."""

    area_m2: float
    rings: list[list[list[float]]]
    objectid: int | None = None
    wkid: int = MGA_ZONE_50
    # Number of cadastral lots combined into this parcel (one address can span several)
    lot_count: int = 1


async def get_lot_parcel(lat: float, lng: float) -> LotParcel | None:
    """Return the cadastral lot containing (lat, lng) with its area + geometry.

    Returns None when the point is not inside a lot (e.g. road reserve) or the
    lookup fails. A failure must never break the chat flow.
    """
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "objectid",
        "returnGeometry": "true",
        "outSR": str(MGA_ZONE_50),
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.get(_CADASTRE_QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Lot lookup failed for (lat=%s, lng=%s)", lat, lng)
        return None

    if data.get("error"):
        logger.error("Lot lookup returned an error: %s", data["error"])
        return None

    features = data.get("features") or []
    if not features:
        logger.info("Lot lookup: no parcel at (lat=%s, lng=%s)", lat, lng)
        return None
    if len(features) > 1:
        logger.info("Lot lookup: %s parcels touch the pin, using the first", len(features))

    spatial_ref = data.get("spatialReference") or {}
    wkid = spatial_ref.get("latestWkid") or spatial_ref.get("wkid")
    if wkid != MGA_ZONE_50:
        logger.warning("Lot lookup: unexpected spatial reference %s", wkid)
        return None

    rings = (features[0].get("geometry") or {}).get("rings") or []
    area = round(polygon_area(rings), 1)
    if area <= 0:
        return None

    objectid = (features[0].get("attributes") or {}).get("objectid")
    logger.info(
        "Lot lookup ok: objectid=%s area=%.1f m² at (lat=%s, lng=%s)",
        objectid,
        area,
        lat,
        lng,
    )
    return LotParcel(area_m2=area, rings=rings, objectid=objectid)


async def get_lot_area_m2(lat: float, lng: float) -> float | None:
    """Area (m²) of the cadastral lot containing (lat, lng), or None."""
    parcel = await get_lot_parcel(lat, lng)
    return parcel.area_m2 if parcel else None


_ADDRESS_LOT_QUERY_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/Places_and_Addresses/MapServer/4/query"
)


async def get_lot_by_land_id(land_id: int) -> LotParcel | None:
    """Exact lot polygon for one Landgate ``land_id``."""
    return await get_lots_by_land_ids([land_id])


async def get_lots_by_land_ids(land_ids: list[int]) -> LotParcel | None:
    """Combined parcel for every lot at an address (from the address search).

    Uses the Cadastre Address layer (LGATE-002), which carries the lot
    polygons keyed by land_id. The rings of all lots are kept together, so the
    area is the total site area and the heritage check covers every lot.
    Returns None on failure so callers can fall back to the point-in-lot lookup.
    """
    ids = sorted({int(i) for i in land_ids})[:50]
    if not ids:
        return None
    params = {
        "where": f"land_id IN ({','.join(str(i) for i in ids)})",
        "outFields": "land_id",
        "returnGeometry": "true",
        "outSR": str(MGA_ZONE_50),
        "f": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.get(_ADDRESS_LOT_QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Lot lookup by land_ids=%s failed", ids)
        return None

    if data.get("error"):
        logger.error("Lot lookup by land_id returned an error: %s", data["error"])
        return None
    features = data.get("features") or []
    if not features:
        logger.info("Lot lookup: no lot for land_ids=%s", ids)
        return None

    spatial_ref = data.get("spatialReference") or {}
    wkid = spatial_ref.get("latestWkid") or spatial_ref.get("wkid")
    if wkid != MGA_ZONE_50:
        logger.warning("Lot lookup by land_id: unexpected spatial reference %s", wkid)
        return None

    rings: list[list[list[float]]] = []
    found: set[int] = set()
    for feature in features:
        lot_id = (feature.get("attributes") or {}).get("land_id")
        if lot_id in found:
            continue  # same lot can appear more than once
        found.add(lot_id)
        rings.extend((feature.get("geometry") or {}).get("rings") or [])
    area = round(polygon_area(rings), 1)
    if area <= 0:
        return None
    logger.info("Lot lookup ok: land_ids=%s lots=%s area=%.1f m²", ids, len(found), area)
    return LotParcel(area_m2=area, rings=rings, objectid=ids[0], lot_count=len(found))
