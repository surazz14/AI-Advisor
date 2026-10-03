"""Point-in-polygon check against the Plantagenet Bush Fire Prone Area map.

Source file: OBRM 024 (2025 extract), LGA PLANTAGENET, CRS EPSG:4283 (GDA94).
Coordinates from address search are WGS84. At property scale in WA the
difference is well under the map's boundary precision, so points are tested
directly. This is a yes/no designation flag, not a BAL assessment.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "bushfire_prone_plantagenet_2025.geojson"
)


@dataclass(frozen=True)
class BushfireStatus:
    inside: bool
    latest_date: str | None = None
    designation: str | None = None


@lru_cache(maxsize=1)
def _areas() -> list[tuple[object, dict]]:
    if not _DATA_PATH.is_file():
        logger.warning("Bushfire map missing at %s", _DATA_PATH)
        return []

    from shapely.geometry import shape
    from shapely.prepared import prep

    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    areas: list[tuple[object, dict]] = []
    for feature in payload.get("features") or []:
        geometry = feature.get("geometry")
        if not geometry:
            continue
        props = feature.get("properties") or {}
        areas.append((prep(shape(geometry)), props))
    logger.info("Bushfire map loaded: %s polygons from %s", len(areas), _DATA_PATH.name)
    return areas


def bushfire_status(lat: float | None, lng: float | None) -> BushfireStatus | None:
    """Return whether (lat, lng) falls in a mapped Bush Fire Prone Area.

    None means the map could not be loaded. A result with inside=False means
    the point was tested and is outside every polygon.
    """
    if lat is None or lng is None:
        return None

    areas = _areas()
    if not areas:
        return None

    from shapely.geometry import Point

    point = Point(float(lng), float(lat))
    hits = [props for geom, props in areas if geom.covers(point)]
    if not hits:
        return BushfireStatus(inside=False)

    def _date(props: dict) -> str:
        raw = str(props.get("designationdate") or "")
        return raw[:10]

    latest = max(hits, key=_date)
    return BushfireStatus(
        inside=True,
        latest_date=_date(latest) or None,
        designation=str(latest.get("designation") or "").strip() or None,
    )
