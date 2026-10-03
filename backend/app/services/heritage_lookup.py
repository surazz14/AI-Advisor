"""Heritage overlay check against WA SLIP "People and Society" layers.

https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/People_and_Society/MapServer

Statutory listings (affect approvals / exemptions):
  7  Heritage Council WA - State Register (DPLH-006)
  16 Heritage List (DPLH-090)            — the Shire's scheme Heritage List
  15 Heritage Areas (DPLH-089)
Information only:
  9  Heritage Council WA - Local Heritage Survey (DPLH-008)
Aboriginal heritage (Aboriginal Heritage Act 1972):
  18 Aboriginal Cultural Heritage - Register (DPLH-099)
  19 Aboriginal Cultural Heritage - Lodged (DPLH-100)

Heritage polygons often outline a building, not the whole lot, so a pin
lookup would miss them. When the cadastral lot is known we query with the lot
polygon instead, then drop neighbours that only touch the shared boundary.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field

import httpx

from app.services.lot_lookup import MGA_ZONE_50

logger = logging.getLogger(__name__)

_BASE_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/People_and_Society/MapServer"
)
_TIMEOUT_SECONDS = 8.0
# Heritage features within this distance of the lot boundary are treated as
# "touching only" (shared boundary with a neighbour), not as on the lot.
_EDGE_TOLERANCE_M = 1.0

STATE_REGISTER = "state_register"
HERITAGE_LIST = "heritage_list"
HERITAGE_AREA = "heritage_area"
LOCAL_SURVEY = "local_heritage_survey"
ABORIGINAL_REGISTER = "aboriginal_register"
ABORIGINAL_LODGED = "aboriginal_lodged"


@dataclass(frozen=True)
class _Layer:
    layer_id: int
    kind: str
    label: str
    aboriginal: bool = False


_LAYERS: tuple[_Layer, ...] = (
    _Layer(7, STATE_REGISTER, "State Register of Heritage Places"),
    _Layer(16, HERITAGE_LIST, "Shire Heritage List"),
    _Layer(15, HERITAGE_AREA, "Heritage Area"),
    _Layer(9, LOCAL_SURVEY, "Local Heritage Survey (information only)"),
    _Layer(18, ABORIGINAL_REGISTER, "Registered Aboriginal heritage place", True),
    _Layer(19, ABORIGINAL_LODGED, "Lodged Aboriginal heritage place", True),
)

_STATUTORY_KINDS = {STATE_REGISTER, HERITAGE_LIST, HERITAGE_AREA}
_ABORIGINAL_KINDS = {ABORIGINAL_REGISTER, ABORIGINAL_LODGED}

_HERITAGE_FIELDS = "objectid,place_no,place_name,location,more_info"
_ABORIGINAL_FIELDS = "objectid,id,name,place_type,culturally_sensitive,restricted_place"


@dataclass
class HeritageMatch:
    kind: str
    label: str
    place_name: str | None = None
    place_no: str | None = None
    location: str | None = None
    url: str | None = None

    def describe(self) -> str:
        if self.place_name:
            ref = f" #{self.place_no}" if self.place_no else ""
            return f"{self.label} — {self.place_name}{ref}"
        return self.label


@dataclass
class HeritageInfo:
    matches: list[HeritageMatch] = field(default_factory=list)
    # "lot" = checked against the lot boundary; "pin" = only the address point
    checked_with: str = "lot"
    # True when some layers could not be queried (result may be incomplete)
    incomplete: bool = False

    @property
    def statutory(self) -> list[HeritageMatch]:
        return [m for m in self.matches if m.kind in _STATUTORY_KINDS]

    @property
    def aboriginal(self) -> list[HeritageMatch]:
        return [m for m in self.matches if m.kind in _ABORIGINAL_KINDS]

    @property
    def survey_only(self) -> list[HeritageMatch]:
        return [m for m in self.matches if m.kind == LOCAL_SURVEY]

    @property
    def has_any(self) -> bool:
        return bool(self.matches)

    def kinds(self) -> list[str]:
        return sorted({m.kind for m in self.matches})


# --- geometry helpers (pure python, metres) ---------------------------------


def _point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_cross:
                inside = not inside
    return inside


def point_in_polygon(x: float, y: float, rings: list[list[list[float]]]) -> bool:
    """Even-odd rule over all rings (holes handled automatically)."""
    inside = False
    for ring in rings:
        if _point_in_ring(x, y, ring):
            inside = not inside
    return inside


def _dist_to_segment(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    cx, cy = x1 + t * dx, y1 + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def distance_to_boundary(x: float, y: float, rings: list[list[list[float]]]) -> float:
    best = float("inf")
    for ring in rings:
        for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:] + ring[:1]):
            best = min(best, _dist_to_segment(x, y, x1, y1, x2, y2))
    return best


def _strictly_inside(x, y, rings, tol) -> bool:
    return point_in_polygon(x, y, rings) and distance_to_boundary(x, y, rings) > tol


def _centroid(rings: list[list[list[float]]]) -> tuple[float, float]:
    pts = [p for ring in rings for p in ring]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def overlaps_lot(
    lot_rings: list[list[list[float]]],
    feature_rings: list[list[list[float]]],
    *,
    tol: float = _EDGE_TOLERANCE_M,
) -> bool:
    """True if a heritage polygon genuinely overlaps the lot (not just touches).

    - a heritage vertex well inside the lot (building outline on the lot), or
    - a lot vertex well inside the heritage polygon (place/area covers lot), or
    - the lot centroid inside the heritage polygon (identical / covering shape).
    """
    if not lot_rings or not feature_rings:
        return False
    for ring in feature_rings:
        for x, y, *_ in ring:
            if _strictly_inside(x, y, lot_rings, tol):
                return True
    for ring in lot_rings:
        for x, y, *_ in ring:
            if _strictly_inside(x, y, feature_rings, tol):
                return True
    cx, cy = _centroid(lot_rings)
    return point_in_polygon(cx, cy, feature_rings)


# --- SLIP queries ------------------------------------------------------------


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _to_match(layer: _Layer, attrs: dict) -> HeritageMatch:
    if layer.aboriginal:
        sensitive = str(attrs.get("culturally_sensitive") or "").lower() == "yes"
        restricted = str(attrs.get("restricted_place") or "").lower() == "yes"
        if sensitive or restricted:
            # Don't reveal names/details of restricted or sensitive places
            return HeritageMatch(kind=layer.kind, label=layer.label)
        return HeritageMatch(
            kind=layer.kind,
            label=layer.label,
            place_name=_clean(attrs.get("name")),
            place_no=_clean(attrs.get("id")),
        )
    return HeritageMatch(
        kind=layer.kind,
        label=layer.label,
        place_name=_clean(attrs.get("place_name")),
        place_no=_clean(attrs.get("place_no")),
        location=_clean(attrs.get("location")),
        url=_clean(attrs.get("more_info")),
    )


async def _query_layer(
    client: httpx.AsyncClient,
    layer: _Layer,
    *,
    lat: float,
    lng: float,
    lot_rings: list[list[list[float]]] | None,
) -> list[HeritageMatch] | None:
    """Matches for one layer, or None if the query failed."""
    fields = _ABORIGINAL_FIELDS if layer.aboriginal else _HERITAGE_FIELDS
    if lot_rings:
        data = {
            "geometry": json.dumps(
                {"rings": lot_rings, "spatialReference": {"wkid": MGA_ZONE_50}}
            ),
            "geometryType": "esriGeometryPolygon",
            "inSR": str(MGA_ZONE_50),
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": fields,
            "returnGeometry": "true",
            "outSR": str(MGA_ZONE_50),
            "f": "json",
        }
    else:
        data = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": fields,
            "returnGeometry": "false",
            "f": "json",
        }

    url = f"{_BASE_URL}/{layer.layer_id}/query"
    try:
        # POST: lot polygons can exceed URL length limits
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        logger.exception("Heritage lookup failed for layer %s", layer.layer_id)
        return None
    if payload.get("error"):
        logger.error("Heritage layer %s error: %s", layer.layer_id, payload["error"])
        return None

    matches: list[HeritageMatch] = []
    seen: set[str] = set()
    for feature in payload.get("features") or []:
        if lot_rings:
            rings = (feature.get("geometry") or {}).get("rings") or []
            if not overlaps_lot(lot_rings, rings):
                continue  # neighbour that only shares a boundary
        match = _to_match(layer, feature.get("attributes") or {})
        key = f"{match.kind}:{match.place_no or match.place_name or len(matches)}"
        if key in seen:
            continue
        seen.add(key)
        matches.append(match)
    return matches


async def get_heritage(
    lat: float,
    lng: float,
    *,
    lot_rings: list[list[list[float]]] | None = None,
) -> HeritageInfo | None:
    """Heritage listings on the lot (or at the pin if the lot is unknown).

    Returns None only when every layer query failed (status unknown).
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
        results = await asyncio.gather(
            *(
                _query_layer(client, layer, lat=lat, lng=lng, lot_rings=lot_rings)
                for layer in _LAYERS
            )
        )

    if all(r is None for r in results):
        return None
    info = HeritageInfo(
        matches=[m for r in results if r for m in r],
        checked_with="lot" if lot_rings else "pin",
        incomplete=any(r is None for r in results),
    )
    logger.info(
        "Heritage lookup (%s) at (lat=%s, lng=%s): %s",
        info.checked_with,
        lat,
        lng,
        [m.describe() for m in info.matches] or "none",
    )
    return info
