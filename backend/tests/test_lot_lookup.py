"""Unit tests for lot area maths (no network)."""

import pytest

from app.services.lot_lookup import format_lot_area, polygon_area, ring_signed_area

# Esri orientation: outer ring clockwise, hole counter-clockwise (closed rings)
SQUARE_100M_CW = [[0, 0], [0, 100], [100, 100], [100, 0], [0, 0]]
HOLE_10M_CCW = [[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]


def test_square_area():
    assert polygon_area([SQUARE_100M_CW]) == pytest.approx(10_000)


def test_orientation_sign():
    assert ring_signed_area(SQUARE_100M_CW) < 0
    assert ring_signed_area(HOLE_10M_CCW) > 0


def test_hole_is_subtracted():
    assert polygon_area([SQUARE_100M_CW, HOLE_10M_CCW]) == pytest.approx(9_900)


def test_unclosed_ring_and_degenerate():
    assert polygon_area([SQUARE_100M_CW[:-1]]) == pytest.approx(10_000)
    assert polygon_area([[[0, 0], [1, 1]]]) == 0
    assert polygon_area([]) == 0


def test_real_slip_parcel_shape():
    # Approximate shape of a 3,235 m² Mount Barker lot (MGA50 metres)
    ring = [[0, 0], [0, 64.7], [50, 64.7], [50, 0], [0, 0]]
    assert polygon_area([ring]) == pytest.approx(3_235, rel=1e-3)


@pytest.mark.parametrize(
    ("area", "expected"),
    [
        (None, None),
        (0, None),
        (3235.0, "3,235 m² (≈0.32 ha)"),
        (40_500.0, "4.05 ha (40,500 m²)"),
    ],
)
def test_format_lot_area(area, expected):
    assert format_lot_area(area) == expected
