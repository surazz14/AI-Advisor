"""Live planning-zone lookup against WA DPLH's public "Local Planning
Scheme - Zones and Reserves" ArcGIS REST layer. No local dataset needed --
this queries a single point directly against the state government's
public map service.

Layer (verified working, field names confirmed against its metadata):
https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/Property_and_Planning/MapServer/112

Note: this is the "Government Use Only" data licensing tier's *map
service*, which is public/open access -- it's the bulk downloads
(Shapefile/GeoJSON/WFS) of the same dataset that require a Data WA
account and accepting DPLH's terms, not this live query endpoint.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

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
    zone_number: int | None = None
    label_description: str | None = None
    scheme_name: str | None = None
    scheme_number: str | None = None
    lga: str | None = None
    gazettal_date: str | None = None


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
        # The layer returns whitespace-only strings for some blank fields
        # (not empty strings, not null) -- strip those down to None so
        # callers can rely on plain truthiness checks.
        if not isinstance(value, str):
            return None
        value = value.strip()
        return value or None

    attrs = features[0].get("attributes", {})
    return ZoneInfo(
        zone=_clean(attrs.get("zone")),
        zone_number=attrs.get("zone_numbe"),
        label_description=_clean(attrs.get("label_desc")),
        scheme_name=_clean(attrs.get("scheme_nam")),
        scheme_number=_clean(attrs.get("scheme_no")),
        lga=_clean(attrs.get("lga")),
        gazettal_date=attrs.get("gazettal_d"),
    )
