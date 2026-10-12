"""Unit tests for Landgate address parsing (no network)."""

import pytest

from app.schemas.messages import ChatSend
from app.services.address_search import _label, group_by_address, parse_address, where_candidates
from app.services.session_store import SessionStore


@pytest.mark.parametrize(
    ("query", "number", "unit", "lot", "road", "road_type", "locality"),
    [
        ("297 seymour road denbarker 6324", "297", None, None, ["seymour"], "RD", "denbarker"),
        ("297 Seymour Rd, Denbarker WA", "297", None, None, ["Seymour"], "RD", "Denbarker"),
        ("2/297 seymour rd", "297", "2", None, ["seymour"], "RD", None),
        ("unit 4/12a Lowood Road Mount Barker", "12A", "4", None, ["Lowood"], "RD", "Mount Barker"),
        ("22-24 Lowood Road Mount Barker", "22", None, None, ["Lowood"], "RD", "Mount Barker"),
        ("Lot 5 Seymour Road", None, None, "5", ["Seymour"], "RD", None),
        ("297 seymour denbarker", "297", None, None, ["seymour", "denbarker"], None, None),
        ("Seymour Road Denbarker", None, None, None, ["Seymour"], "RD", "Denbarker"),
    ],
)
def test_parse_address(query, number, unit, lot, road, road_type, locality):
    p = parse_address(query)
    assert p is not None
    assert (p.number, p.unit, p.lot) == (number, unit, lot)
    assert p.road_words == road
    assert p.road_type == road_type
    assert p.locality == locality


@pytest.mark.parametrize("query", ["", "297", "mount barker", "a"])
def test_parse_address_nothing_to_search(query):
    assert parse_address(query) is None


def test_where_candidates_exact():
    clauses = where_candidates(parse_address("297 seymour road denbarker"))
    assert clauses[0] == (
        "road_number_1 = '297' AND road_type = 'RD' AND "
        "road_name LIKE 'SEYMOUR%' AND locality LIKE 'DENBARKER%'"
    )
    # Falls back to dropping the locality
    assert clauses[1] == "road_number_1 = '297' AND road_type = 'RD' AND road_name LIKE 'SEYMOUR%'"


def test_where_candidates_without_road_type():
    clauses = where_candidates(parse_address("297 seymour denbarker"))
    assert "road_name LIKE 'SEYMOUR DENBARKER%'" in clauses[0]
    assert clauses[1].endswith("road_name LIKE 'SEYMOUR%' AND locality LIKE 'DENBARKER%'")


def test_where_escapes_quotes():
    clauses = where_candidates(parse_address("3 O'Neill Road"))
    assert "road_name LIKE 'O''NEILL%'" in clauses[0]


def test_label_keeps_unit_and_lot():
    attrs = {"road_number_1": "297", "road_name": "SEYMOUR", "road_type": "RD", "locality": "DENBARKER"}
    assert _label(attrs, parse_address("2/297 seymour rd")) == "2/297 Seymour Rd, Denbarker WA"
    lot_attrs = {"road_number_1": None, "lot_number": "5", "road_name": "SEYMOUR",
                 "road_type": "RD", "locality": "DENBARKER"}
    assert _label(lot_attrs, parse_address("lot 5 seymour rd")) == "Lot 5 Seymour Rd, Denbarker WA"


def test_session_resets_lot_when_land_ids_change():
    store = SessionStore()
    ctx = store.upsert("s1", address="1 Lowood Rd", lat=-34.6, lng=117.6, land_ids=[2, 1])
    store.set_parcel_facts("s1", lot_area_m2=100.0, rcode=None, lot_count=2)
    assert ctx.parcel_checked and ctx.land_ids == (1, 2) and ctx.lot_count == 2
    store.upsert("s1", address="1 Lowood Rd", lat=-34.6, lng=117.6, land_ids=[1, 2])
    assert ctx.parcel_checked  # same lots, different order → keep cached facts
    store.upsert("s1", address="1 Lowood Rd", lat=-34.6, lng=117.6, land_ids=[3])
    assert not ctx.parcel_checked and ctx.land_ids == (3,) and ctx.lot_count == 1


def _lot(land_id, x0, size, number="1"):
    ring = [[x0, 0], [x0, size], [x0 + size, size], [x0 + size, 0], [x0, 0]]
    return {
        "attributes": {"land_id": land_id, "road_number_1": number, "road_number_2": None,
                       "lot_number": None, "road_name": "LOWOOD", "road_type": "RD",
                       "locality": "MOUNT BARKER"},
        "geometry": {"rings": [ring]},
    }


def test_group_by_address_merges_lots_sharing_an_address():
    groups = group_by_address([
        _lot(10, 0, 10),            # 100
        _lot(11, 20, 30),           # 900 — largest, should lead the group
        _lot(12, 60, 5, number="3"),
        _lot(10, 0, 10),            # duplicate row
    ])
    assert [[land_id for land_id, _, _ in g] for g in groups] == [[11, 10], [12]]


def test_lot_ids_accepts_list_and_legacy_single_id():
    base = {"type": "chat.send", "sessionId": "s", "content": "hi"}
    assert ChatSend(**base, landIds=[1, 2]).lot_ids == [1, 2]
    assert ChatSend(**base, landId=7).lot_ids == [7]
    assert ChatSend(**base).lot_ids is None
