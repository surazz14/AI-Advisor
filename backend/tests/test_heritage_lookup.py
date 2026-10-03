"""Unit tests for heritage overlap + listing logic (no network)."""

from app.services.heritage_lookup import (
    HERITAGE_LIST,
    LOCAL_SURVEY,
    STATE_REGISTER,
    HeritageInfo,
    HeritageMatch,
    _LAYERS,
    _to_match,
    overlaps_lot,
    point_in_polygon,
)

# 50 m x 60 m lot, Esri clockwise
LOT = [[[0, 0], [0, 60], [50, 60], [50, 0], [0, 0]]]


def _square(x0, y0, x1, y1):
    return [[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]]


def test_point_in_polygon():
    assert point_in_polygon(25, 30, LOT)
    assert not point_in_polygon(60, 30, LOT)


def test_building_outline_inside_lot_matches():
    assert overlaps_lot(LOT, _square(10, 10, 20, 25))


def test_neighbour_sharing_boundary_is_ignored():
    # Lot to the east shares the x=50 boundary exactly
    assert not overlaps_lot(LOT, _square(50, 0, 100, 60))


def test_neighbour_with_small_survey_error_is_ignored():
    # Neighbour polygon pokes 0.4 m over the line (digitising noise)
    assert not overlaps_lot(LOT, _square(49.6, 0, 100, 60))


def test_heritage_area_covering_lot_matches():
    assert overlaps_lot(LOT, _square(-100, -100, 200, 200))


def test_identical_polygon_matches():
    assert overlaps_lot(LOT, LOT)


def test_far_away_polygon_does_not_match():
    assert not overlaps_lot(LOT, _square(500, 500, 520, 520))


def _layer(kind):
    return next(layer for layer in _LAYERS if layer.kind == kind)


def test_heritage_match_fields_are_cleaned():
    match = _to_match(
        _layer(STATE_REGISTER),
        {"place_no": 2268.0, "place_name": " Police Station and Gaol Complex (fmr) ", "more_info": "https://inherit.dplh.wa.gov.au/x"},
    )
    assert match.place_no == "2268"
    assert match.place_name == "Police Station and Gaol Complex (fmr)"
    assert "State Register" in match.describe()


def test_restricted_aboriginal_place_hides_details():
    layer = next(layer for layer in _LAYERS if layer.aboriginal)
    hidden = _to_match(layer, {"name": "SECRET", "id": "1", "restricted_place": "Yes", "culturally_sensitive": "No"})
    shown = _to_match(layer, {"name": "SCARRED TREE", "id": "2", "restricted_place": "No", "culturally_sensitive": "No"})
    assert hidden.place_name is None and "SECRET" not in hidden.describe()
    assert shown.place_name == "SCARRED TREE"


def test_heritage_info_groups():
    info = HeritageInfo(
        matches=[
            HeritageMatch(kind=HERITAGE_LIST, label="Shire Heritage List", place_name="A"),
            HeritageMatch(kind=LOCAL_SURVEY, label="Local Heritage Survey", place_name="A"),
        ]
    )
    assert [m.kind for m in info.statutory] == [HERITAGE_LIST]
    assert [m.kind for m in info.survey_only] == [LOCAL_SURVEY]
    assert info.aboriginal == []
    assert HeritageInfo().has_any is False
