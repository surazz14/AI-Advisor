"""Bush Fire Prone Area check against the Plantagenet designation map.

Source file: OBRM 024 (2025 extract), LGA PLANTAGENET, CRS EPSG:4283 (GDA94).
This is a yes/no designation flag, not a BAL assessment.

A property counts as bushfire prone when ANY part of the lot is inside a
mapped Bush Fire Prone Area, so when the lot boundary is known we test the
whole lot, not just the address pin. A pin can easily sit in the unmapped
part of a mostly-designated lot (e.g. 297 Seymour Rd, Denbarker: ~88% of
the lot is designated but its centre point is ~20 m outside).
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "bushfire_prone_plantagenet_2025.geojson"
)

# Lot rings from the cadastre lookups are GDA2020 / MGA zone 50 (metres)
_LOT_WKID = 7850
_MAP_CRS = "EPSG:4283"
# Ignore slivers smaller than this (map edges vs lot boundaries don't line up exactly)
_MIN_OVERLAP_M2 = 5.0


@dataclass(frozen=True)
class BushfireStatus:
    inside: bool
    latest_date: str | None = None
    designation: str | None = None
    # Share of the lot inside the mapped area (0–1); None when only the pin was tested
    lot_share: float | None = None

    @property
    def partial(self) -> bool:
        """True when only part of the lot is mapped as bushfire prone."""
        return self.inside and self.lot_share is not None and self.lot_share < 0.99


@lru_cache(maxsize=1)
def _areas() -> list[tuple[object, object, dict]]:
    """(geometry, prepared geometry, properties) for every mapped polygon."""
    if not _DATA_PATH.is_file():
        logger.warning("Bushfire map missing at %s", _DATA_PATH)
        return []

    from shapely.geometry import shape
    from shapely.prepared import prep

    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    areas: list[tuple[object, object, dict]] = []
    for feature in payload.get("features") or []:
        geometry = feature.get("geometry")
        if not geometry:
            continue
        props = feature.get("properties") or {}
        geom = shape(geometry)
        areas.append((geom, prep(geom), props))
    logger.info("Bushfire map loaded: %s polygons from %s", len(areas), _DATA_PATH.name)
    return areas


def _date(props: dict) -> str:
    return str(props.get("designationdate") or "")[:10]


def _status_from_hits(hits: list[dict], lot_share: float | None) -> BushfireStatus:
    if not hits:
        return BushfireStatus(inside=False, lot_share=lot_share)
    latest = max(hits, key=_date)
    return BushfireStatus(
        inside=True,
        latest_date=_date(latest) or None,
        designation=str(latest.get("designation") or "").strip() or None,
        lot_share=lot_share,
    )


def bushfire_status(lat: float | None, lng: float | None) -> BushfireStatus | None:
    """Whether a single point falls in a mapped Bush Fire Prone Area.

    Prefer :func:`bushfire_status_for_lot` when the lot boundary is known.
    None means the map could not be loaded.
    """
    if lat is None or lng is None:
        return None

    areas = _areas()
    if not areas:
        return None

    from shapely.geometry import Point

    point = Point(float(lng), float(lat))
    hits = [props for _, prepared, props in areas if prepared.covers(point)]
    return _status_from_hits(hits, None)


@lru_cache(maxsize=1)
def _to_map_crs():
    from pyproj import Transformer

    return Transformer.from_crs(f"EPSG:{_LOT_WKID}", _MAP_CRS, always_xy=True)


def lot_geometry_lonlat(rings: list[list[list[float]]]):
    """Lot rings (MGA zone 50 metres) → a shapely geometry in the map's lon/lat.

    Esri polygons store outer rings clockwise and holes anticlockwise; rings
    from several lots are simply several outer rings. The result is the union
    of the outer rings minus the holes. None when nothing valid is left.
    """
    from shapely.geometry import LinearRing, Polygon
    from shapely.ops import unary_union

    transformer = _to_map_crs()
    outers, holes = [], []
    for ring in rings:
        if len(ring) < 3:
            continue
        xy = [(p[0], p[1]) for p in ring]
        try:
            is_hole = LinearRing(xy).is_ccw
        except ValueError:
            continue
        lons, lats = transformer.transform(*zip(*xy))
        poly = Polygon(zip(lons, lats))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        (holes if is_hole else outers).append(poly)
    if not outers:
        return None
    geom = unary_union(outers)
    if holes:
        geom = geom.difference(unary_union(holes))
    return None if geom.is_empty else geom


def _deg2_to_m2(area_deg2: float, lat: float) -> float:
    """Approximate m² for a small area in degrees² at latitude ``lat``."""
    return area_deg2 * 111_320.0 * 110_574.0 * math.cos(math.radians(lat))


def bushfire_status_for_geometry(lot) -> BushfireStatus | None:
    """Bushfire status for a lot geometry already in the map's lon/lat."""
    areas = _areas()
    if not areas or lot is None or lot.is_empty:
        return None

    lat = lot.centroid.y
    lot_area = lot.area
    hits: list[dict] = []
    overlap = 0.0
    for geom, prepared, props in areas:
        if not prepared.intersects(lot):
            continue
        part = geom.intersection(lot).area
        if _deg2_to_m2(part, lat) >= _MIN_OVERLAP_M2:
            hits.append(props)
            overlap += part
    share = min(overlap / lot_area, 1.0) if lot_area > 0 else None
    return _status_from_hits(hits, round(share, 3) if share is not None else None)


def bushfire_status_for_lot(
    rings: list[list[list[float]]] | None,
    lat: float | None,
    lng: float | None,
) -> BushfireStatus | None:
    """Bushfire status for the whole lot, falling back to the pin.

    ``rings`` are the lot rings in MGA zone 50 from the cadastre lookups.
    """
    if rings:
        try:
            status = bushfire_status_for_geometry(lot_geometry_lonlat(rings))
            if status is not None:
                logger.info(
                    "Bushfire check (lot): inside=%s share=%s", status.inside, status.lot_share
                )
                return status
        except Exception:
            logger.exception("Bushfire lot check failed — falling back to the pin")
    return bushfire_status(lat, lng)
