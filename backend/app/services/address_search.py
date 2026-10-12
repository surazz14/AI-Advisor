"""Exact property address search via Landgate's Cadastre Address layer.

Layer: "Cadastre Address (LGATE-002) - Large Scale" on WA SLIP
https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/Places_and_Addresses/MapServer/4

Each feature is a cadastral lot polygon carrying its street address
(road_number_1/2, road_name, road_type, locality) and lot_number, so a match
gives the exact lot — not just a point on the road like OpenStreetMap often
does for rural WA. We return a point guaranteed to be inside the lot plus the
Landgate ``land_id`` so the backend can reuse the exact lot boundary.

One address can cover several lots (e.g. 1 Lowood Rd, Mount Barker sits on
three lots). Those are merged into one suggestion carrying every land_id, so
the backend can treat the whole property as one site.

Units: the layer has no unit field. Strata units sit on the parent lot, so a
"2/297 Seymour Rd" search resolves to the lot for 297 and keeps the unit in
the label.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

ADDRESS_QUERY_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/Places_and_Addresses/MapServer/4/query"
)
_TIMEOUT_SECONDS = 8.0

# Shire of Plantagenet bounding box (lng/lat) — same as src/lib/plantagenetScope.ts.
# The backend still confirms the LGA from the zone layer when the chat starts.
PLANTAGENET_ENVELOPE = "117.15,-34.88,117.95,-34.40"

_OUT_FIELDS = "land_id,road_number_1,road_number_2,lot_number,road_name,road_type,locality"

ROAD_TYPES: dict[str, str] = {
    "road": "RD", "rd": "RD",
    "street": "ST", "st": "ST",
    "avenue": "AVE", "ave": "AVE", "av": "AVE",
    "drive": "DR", "dr": "DR",
    "lane": "LANE", "ln": "LANE",
    "court": "CT", "ct": "CT",
    "place": "PL", "pl": "PL",
    "highway": "HWY", "hwy": "HWY",
    "terrace": "TCE", "tce": "TCE",
    "way": "WAY",
    "crescent": "CRES", "cres": "CRES", "cr": "CRES",
    "close": "CL", "cl": "CL",
    "parade": "PDE", "pde": "PDE",
    "boulevard": "BVD", "bvd": "BVD", "blvd": "BVD",
    "circuit": "CCT", "cct": "CCT",
    "grove": "GR", "gr": "GR",
    "loop": "LOOP",
    "rise": "RISE",
    "track": "TRK", "trk": "TRK",
    "gardens": "GDNS", "gdns": "GDNS",
    "square": "SQ", "sq": "SQ",
    "view": "VIEW",
    "vista": "VSTA",
    "retreat": "RTT",
    "esplanade": "ESP", "esp": "ESP",
    "mews": "MEWS",
    "chase": "CH",
    "bend": "BEND",
    "brace": "BRCE",
    "heights": "HTS",
}

# "297 ...", "2/297 ...", "unit 2/297 ...", "22-24 ...", "12a ..."
_STREET_NUMBER = re.compile(
    r"^(?:(?:unit|u|apt|apartment|flat)\s*)?"
    r"(?:(?P<unit>\d+[a-z]?)\s*/\s*)?"
    r"(?P<number>\d+[a-z]?)(?:\s*[-–]\s*\d+[a-z]?)?\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
# "lot 5 ...", "lot 5, ..."
_LOT_NUMBER = re.compile(r"^lot\s*(?P<lot>\d+[a-z]?)\s+(?P<rest>.+)$", re.IGNORECASE)


@dataclass
class ParsedAddress:
    road_words: list[str]
    road_type: str | None = None
    locality: str | None = None
    number: str | None = None
    unit: str | None = None
    lot: str | None = None


def _split_rest(rest: str) -> tuple[list[str], str | None, str | None]:
    """Split 'seymour road denbarker wa 6324' → (['seymour'], 'RD', 'denbarker')."""
    words = [
        w
        for w in re.sub(r"[^\w\s'-]", " ", rest).split()
        if not re.fullmatch(r"\d{4}", w)  # postcode
        and w.lower() not in {"wa", "western", "australia"}
    ]
    road: list[str] = []
    road_type: str | None = None
    locality: list[str] = []
    for word in words:
        if road_type is None and road and word.lower() in ROAD_TYPES:
            road_type = ROAD_TYPES[word.lower()]
        elif road_type is None:
            road.append(word)
        else:
            locality.append(word)
    return road, road_type, (" ".join(locality) or None)


def parse_address(query: str) -> ParsedAddress | None:
    """Parse free text into address parts. None when there is nothing to search."""
    text = " ".join(query.replace(",", " ").split())
    if not text:
        return None

    unit = number = lot = None
    lot_match = _LOT_NUMBER.match(text)
    num_match = _STREET_NUMBER.match(text)
    if lot_match:
        lot, rest = lot_match.group("lot"), lot_match.group("rest")
    elif num_match:
        unit, number, rest = (
            num_match.group("unit"),
            num_match.group("number"),
            num_match.group("rest"),
        )
    else:
        rest = text

    road, road_type, locality = _split_rest(rest)
    if not road or len(" ".join(road)) < 2:
        return None
    # Without a house/lot number we only search when a road type makes it
    # clear the user typed a street (avoids matching every road for "mount barker").
    if number is None and lot is None and road_type is None:
        return None
    return ParsedAddress(
        road_words=road,
        road_type=road_type,
        locality=locality,
        number=number.upper() if number else None,
        unit=unit.upper() if unit else None,
        lot=lot.upper() if lot else None,
    )


def _sql(value: str) -> str:
    """Uppercase + escape for an ArcGIS SQL string literal."""
    return value.upper().replace("'", "''")


def where_candidates(parsed: ParsedAddress) -> list[str]:
    """WHERE clauses to try in order until one returns results.

    The road type is often missing or half-typed ("297 seymour denbarker",
    "297 seymour ro"), so we also try treating the last word as the locality,
    then the road name alone.
    """
    base: list[str] = []
    if parsed.number:
        base.append(f"road_number_1 = '{_sql(parsed.number)}'")
    if parsed.lot:
        base.append(f"lot_number = '{_sql(parsed.lot)}'")
    if parsed.road_type:
        base.append(f"road_type = '{parsed.road_type}'")

    def clause(road: list[str], locality: str | None) -> str:
        parts = [*base, f"road_name LIKE '{_sql(' '.join(road))}%'"]
        if locality:
            parts.append(f"locality LIKE '{_sql(locality)}%'")
        return " AND ".join(parts)

    road = parsed.road_words
    out = [clause(road, parsed.locality)]
    if parsed.road_type is None and len(road) > 1:
        out.append(clause(road[:-1], road[-1]))  # last word = locality
        out.append(clause(road[:1], None))  # first word = road name
    elif parsed.locality:
        out.append(clause(road, None))  # locality typo / suburb vs town
    # De-dupe, keep order
    return list(dict.fromkeys(out))


def _title(value: str | None) -> str:
    return " ".join(w.capitalize() for w in (value or "").split())


def _label(attrs: dict, parsed: ParsedAddress) -> str:
    road = f"{_title(attrs.get('road_name'))} {_title(attrs.get('road_type'))}".strip()
    num = (attrs.get("road_number_1") or "").strip()
    if num and attrs.get("road_number_2"):
        num = f"{num}-{attrs['road_number_2'].strip()}"
    if num:
        street = f"{num} {road}"
        if parsed.unit:
            street = f"{parsed.unit}/{street}"
    elif attrs.get("lot_number"):
        street = f"Lot {attrs['lot_number'].strip()} {road}"
    else:
        street = road
    locality = _title(attrs.get("locality"))
    return f"{street}, {locality} WA" if locality else f"{street}, WA"


def _polygon(rings: list[list[list[float]]]) -> Polygon | None:
    """Shapely polygon for an Esri lot (outer ring + holes), or None."""
    if not rings:
        return None
    try:
        polygon = Polygon(rings[0], rings[1:])
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
    except Exception:
        logger.exception("Could not build lot geometry")
        return None
    return None if polygon.is_empty else polygon


def _address_key(attrs: dict) -> tuple:
    """Lots sharing all of these belong to the same street address."""
    return tuple(
        (attrs.get(k) or "").strip().upper()
        for k in ("road_number_1", "road_number_2", "lot_number", "road_name", "road_type", "locality")
    )


def _number_sort_key(attrs: dict) -> tuple:
    """Sort addresses naturally: 1, 3, 11, 100 (SLIP sorts them as text)."""
    raw = (attrs.get("road_number_1") or attrs.get("lot_number") or "").strip()
    match = re.match(r"(\d+)(.*)", raw)
    number = (int(match.group(1)), match.group(2)) if match else (10**9, raw)
    return ((attrs.get("locality") or ""), (attrs.get("road_name") or ""), number)


def group_by_address(features: list[dict]) -> list[list[tuple[int, Polygon, dict]]]:
    """Group lot features by street address, keeping first-seen order.

    Each group is a list of (land_id, polygon, attrs), largest lot first.
    """
    groups: dict[tuple, list[tuple[int, Polygon, dict]]] = {}
    seen_ids: set[int] = set()
    for feature in features:
        attrs = feature.get("attributes") or {}
        land_id = attrs.get("land_id")
        if land_id is None or land_id in seen_ids:
            continue
        polygon = _polygon((feature.get("geometry") or {}).get("rings") or [])
        if polygon is None:
            continue
        seen_ids.add(land_id)
        groups.setdefault(_address_key(attrs), []).append((int(land_id), polygon, attrs))
    merged = [
        sorted(lots, key=lambda lot: lot[1].area, reverse=True)
        for lots in groups.values()
    ]
    merged.sort(key=lambda lots: _number_sort_key(lots[0][2]))
    return merged


async def _query(client: httpx.AsyncClient, where: str, fetch: int) -> list[dict]:
    params = {
        "where": where,
        "geometry": PLANTAGENET_ENVELOPE,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": _OUT_FIELDS,
        "returnGeometry": "true",
        "outSR": "4326",
        "orderByFields": "locality,road_name,road_number_1",
        "resultRecordCount": str(fetch),
        "f": "json",
    }
    resp = await client.get(ADDRESS_QUERY_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"SLIP address query error: {data['error']}")
    return data.get("features") or []


async def search_addresses(query: str, *, limit: int = 8) -> list[dict]:
    """Exact address suggestions inside the Shire of Plantagenet bbox.

    Raises on network/service failure so callers can fall back to another
    geocoder; returns [] when the text simply matches nothing.
    """
    parsed = parse_address(query)
    if parsed is None:
        return []

    # Fetch extra rows: several lots can share one address and get merged.
    # Road-only searches fetch a whole street, because SLIP orders house
    # numbers as text ("1", "100", "11") and we re-sort them naturally.
    has_number = parsed.number is not None or parsed.lot is not None
    fetch = min(limit * 4, 100) if has_number else 500

    features: list[dict] = []
    async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
        for where in where_candidates(parsed):
            features = await _query(client, where, fetch)
            if features:
                break

    results: list[dict] = []
    for lots in group_by_address(features)[:limit]:
        main_id, main_polygon, attrs = lots[0]
        # Point inside the largest lot: zone / R-Code / bushfire are checked here
        point = main_polygon.representative_point()
        land_ids = [land_id for land_id, _, _ in lots]
        results.append(
            {
                "id": "landgate-" + "-".join(str(i) for i in sorted(land_ids)),
                "label": _label(attrs, parsed),
                "lat": round(point.y, 7),
                "lng": round(point.x, 7),
                "locality": _title(attrs.get("locality")) or None,
                "state": "WA",
                # Every lot at this address, largest first
                "landIds": land_ids,
                "lotCount": len(land_ids),
                "lotNumber": (attrs.get("lot_number") or "").strip() or None,
                "source": "landgate",
            }
        )
    logger.info("Address search q=%r → %s Landgate match(es)", query[:80], len(results))
    return results
