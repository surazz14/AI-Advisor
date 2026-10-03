"""Unit tests for R-Code parsing (no network)."""

import pytest

from app.services.rcode_lookup import parse_rcode


@pytest.mark.parametrize(
    ("raw", "code", "base", "alt"),
    [
        ("R10", "R10", "R10", None),
        ("R2.5", "R2.5", "R2.5", None),
        ("R10/17.5", "R10/17.5", "R10", "R17.5"),
        ("R2.5/20", "R2.5/20", "R2.5", "R20"),
        (" r10 / R17.5 ", "R10/17.5", "R10", "R17.5"),
        ("30", "R30", "R30", None),
    ],
)
def test_parse_rcode(raw, code, base, alt):
    info = parse_rcode(raw)
    assert info is not None
    assert (info.code, info.base, info.alternative) == (code, base, alt)
    assert info.is_dual is (alt is not None)


@pytest.mark.parametrize("raw", [None, "", "  ", "Rural", "R", "R10/abc"])
def test_parse_rcode_rejects_junk(raw):
    assert parse_rcode(raw) is None


def test_describe():
    assert parse_rcode("R10").describe() == "R10"
    assert parse_rcode("R10/17.5").describe() == (
        "R10/17.5 (R10 base; R17.5 if scheme conditions are met)"
    )
