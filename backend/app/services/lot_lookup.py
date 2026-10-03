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
