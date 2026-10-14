"""Bushfire checks test the whole lot, not just the address pin (no network)."""

import pytest
from pyproj import Transformer
from shapely.geometry import box
from shapely.prepared import prep

from app.services import bushfire_lookup as bl

# A small square of "bush fire prone" map near Denbarker (lon/lat, GDA94)
BPA = box(117.340, -34.720, 117.346, -34.710)
PROPS = {"designation": "Bush Fire Prone Area", "designationdate": "2017-06-01T00:00:00Z"}
_TO_MGA = Transformer.from_crs("EPSG:4283", "EPSG:7850", always_xy=True)


@pytest.fixture(autouse=True)
def fake_map(monkeypatch):
    monkeypatch.setattr(bl, "_areas", lambda: [(BPA, prep(BPA), PROPS)])


def mga_ring(lon0, lat0, lon1, lat1, clockwise=True):
    """Rectangle ring in MGA zone 50 metres, Esri style (outer = clockwise)."""
    corners = [(lon0, lat0), (lon0, lat1), (lon1, lat1), (lon1, lat0), (lon0, lat0)]
    if not clockwise:
        corners.reverse()
    return [list(_TO_MGA.transform(x, y)) for x, y in corners]


def test_pin_outside_but_most_of_lot_inside_is_bushfire_prone():
    # Lot straddles the map edge at lon 117.346; the pin is in the unmapped strip
    ring = mga_ring(117.342, -34.716, 117.347, -34.714)
    pin_lat, pin_lng = -34.715, 117.3465
    assert bl.bushfire_status(pin_lat, pin_lng).inside is False

    status = bl.bushfire_status_for_lot([ring], pin_lat, pin_lng)
    assert status.inside is True
    assert status.partial is True
    assert 0.75 < status.lot_share < 0.85
    assert status.latest_date == "2017-06-01"


def test_lot_fully_inside():
    status = bl.bushfire_status_for_lot([mga_ring(117.341, -34.716, 117.343, -34.714)], None, None)
    assert status.inside is True
    assert status.partial is False


def test_lot_outside():
    status = bl.bushfire_status_for_lot([mga_ring(117.350, -34.716, 117.352, -34.714)], None, None)
    assert status.inside is False
    assert status.lot_share == 0


def test_boundary_sliver_is_ignored():
    # Lot only touches the map edge (< 5 m² overlap) — not bushfire prone
    status = bl.bushfire_status_for_lot([mga_ring(117.34599999, -34.716, 117.349, -34.714)], None, None)
    assert status.inside is False


def test_hole_is_subtracted():
    outer = mga_ring(117.344, -34.716, 117.350, -34.714)
    hole = mga_ring(117.344001, -34.71599, 117.3459, -34.71401, clockwise=False)
    without_hole = bl.bushfire_status_for_geometry(bl.lot_geometry_lonlat([outer]))
    with_hole = bl.bushfire_status_for_geometry(bl.lot_geometry_lonlat([outer, hole]))
    # A third of the lot is mapped; the hole removes most of that part
    assert 0.30 < without_hole.lot_share < 0.36
    assert with_hole.lot_share < 0.05


def test_two_lots_one_inside():
    lots = [
        mga_ring(117.341, -34.716, 117.342, -34.715),  # inside the map
        mga_ring(117.350, -34.716, 117.351, -34.715),  # outside
    ]
    status = bl.bushfire_status_for_lot(lots, None, None)
    assert status.inside is True
    assert 0.45 < status.lot_share < 0.55


def test_falls_back_to_pin_without_lot():
    assert bl.bushfire_status_for_lot(None, -34.715, 117.343).inside is True
    assert bl.bushfire_status_for_lot(None, -34.715, 117.360).inside is False
    assert bl.bushfire_status_for_lot(None, None, None) is None
