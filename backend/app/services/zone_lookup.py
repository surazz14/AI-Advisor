"""Live planning-zone lookup against WA DPLH's public "Local Planning
Scheme - Zones and Reserves" ArcGIS REST layer. No local dataset needed --
this queries a single point directly against the state government's
public map service.

Used as a fallback in session_store.upsert(): the dummy GIS pins
(app/services/gis_dummy.py) are tried first, and this live lookup only
runs when they don't match, so the two zone sources compose instead of
competing. Structurally identical to gis_dummy.ZoneInfo (same camelCase
fields + a to_dict()) so either one works anywhere ctx.zone is read.

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


@dataclass
class ZoneInfo:
    zone: str | None = None
    zoneNumber: int | None = None
    labelDescription: str | None = None
    schemeName: str | None = None
    schemeNumber: str | None = None
    lga: str | None = None
    gazettalDate: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


async def get_zone_info(lat: float, lng: float) -> ZoneInfo | None:
    """Look up the planning zone containing (lat, lng).

    Returns None if the point falls outside any mapped zone, or if the
    lookup fails for any reason (network error, unexpected response,
    timeout). Callers should treat that as "zone unknown" rather than as
    an error -- a lookup failure must never break the chat/advisor flow.
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

    return ZoneInfo(
        zone=zone_name,
        zoneNumber=attrs.get("zone_numbe"),
        labelDescription=_clean(attrs.get("label_desc")),
        schemeName=_clean(attrs.get("scheme_nam")),
        schemeNumber=_clean(attrs.get("scheme_no")),
        lga=_clean(attrs.get("lga")),
        gazettalDate=attrs.get("gazettal_d"),
    )