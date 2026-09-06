"""Live planning-zone lookup against WA DPLH's public "Local Planning
Scheme - Zones and Reserves" ArcGIS REST layer.

Primary GIS source for the advisor. Queries a single point against the
state government's public map service.

Layer (verified working, field names confirmed against its metadata):
https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/Property_and_Planning/MapServer/112
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

import httpx

logger = logging.getLogger(__name__)

_ZONE_LAYER_QUERY_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/Property_and_Planning/MapServer/112/query"
)

_TIMEOUT_SECONDS = 6.0

# Real field names from the layer's metadata (name -> alias):
#   zone_numbe -> Zone number, zone -> Zone, label_desc -> Label description,
#   scheme_nam -> Scheme name, scheme_no -> Scheme number, lga -> LGA,
#   gazettal_d -> Gazettal date
_OUT_FIELDS = "zone,zone_numbe,label_desc,scheme_nam,scheme_no,lga,gazettal_d"

OUTSIDE_PLANTAGENET_MESSAGE = (
    "This advisor only covers properties in the Shire of Plantagenet "
    "(for example Mount Barker, Kendenup, Narrikup, Porongurup, or Rocky Gully). "
    "Please choose an address inside the Shire."
)

MISSING_COORDS_MESSAGE = (
    "Please select an address from the suggestions so we can confirm it is "
    "inside the Shire of Plantagenet."
)


@dataclass
class ZoneInfo:
    zone: str
    zoneNumber: int | None = None
    labelDescription: str | None = None
    schemeName: str | None = None
    schemeNumber: str | None = None
    lga: str | None = None
    gazettalDate: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def is_plantagenet_lga(zone: ZoneInfo | None) -> bool:
    """True when SLIP reports this point as Shire of Plantagenet."""
    if not zone:
        return False
    haystack = " ".join(
        part
        for part in (zone.lga, zone.schemeName)
        if isinstance(part, str) and part.strip()
    ).upper()
    return "PLANTAGENET" in haystack


def plantagenet_rejection_reason(
    *,
    lat: float | None,
    lng: float | None,
    zone: ZoneInfo | None,
) -> str | None:
    """Return a user-facing error if the pin is not usable for this advisor."""
    if lat is None or lng is None:
        return MISSING_COORDS_MESSAGE
    if zone is None:
        return OUTSIDE_PLANTAGENET_MESSAGE
    if not is_plantagenet_lga(zone):
        lga = (zone.lga or zone.schemeName or "another local government").strip()
        return (
            f"That location appears to be in {lga}, not the Shire of Plantagenet. "
            + OUTSIDE_PLANTAGENET_MESSAGE
        )
    return None


async def get_zone_info(lat: float, lng: float) -> ZoneInfo | None:
    """Look up the planning zone containing (lat, lng).

    Returns None if the point falls outside any mapped zone, or if the
    lookup fails for any reason (network error, unexpected response,
    timeout). Callers should treat that as "zone unknown" rather than as
    an error — a lookup failure must never break the chat/advisor flow.
    """
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": _OUT_FIELDS,
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.get(_ZONE_LAYER_QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Zone lookup failed for (lat=%s, lng=%s)", lat, lng)
        return None

    if data.get("error"):
        logger.error("Zone lookup returned an error: %s", data["error"])
        return None

    features = data.get("features") or []
    if not features:
        logger.info("Zone lookup: no feature at (lat=%s, lng=%s)", lat, lng)
        return None

    def _clean(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        value = value.strip()
        return value or None

    attrs = features[0].get("attributes", {})
    zone_name = _clean(attrs.get("zone"))
    if not zone_name:
        return None

    zone_number = attrs.get("zone_numbe")
    if zone_number is not None and not isinstance(zone_number, int):
        try:
            zone_number = int(zone_number)
        except (TypeError, ValueError):
            zone_number = None

    gazettal = attrs.get("gazettal_d")
    if gazettal is not None and not isinstance(gazettal, int):
        try:
            gazettal = int(gazettal)
        except (TypeError, ValueError):
            gazettal = None

    info = ZoneInfo(
        zone=zone_name,
        zoneNumber=zone_number,
        labelDescription=_clean(attrs.get("label_desc")),
        schemeName=_clean(attrs.get("scheme_nam")),
        schemeNumber=_clean(attrs.get("scheme_no")),
        lga=_clean(attrs.get("lga")),
        gazettalDate=gazettal,
    )
    logger.info(
        "Zone lookup ok: %s (LGA=%s scheme=%s) at (lat=%s, lng=%s)",
        info.zone,
        info.lga,
        info.schemeName,
        lat,
        lng,
    )
    return info


async def resolve_zone(
    *,
    lat: float | None,
    lng: float | None,
    address: str | None = None,
) -> ZoneInfo | None:
    """Resolve planning zone from coordinates via the live SLIP layer.

    Address is only used for logging — point-in-polygon needs lat/lng.
    """
    if lat is None or lng is None:
        logger.info(
            "Zone resolve skipped (missing coordinates) address=%r",
            address,
        )
        return None
    return await get_zone_info(lat, lng)
