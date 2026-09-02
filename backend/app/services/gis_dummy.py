"""Dummy GIS property facts for two test locations (replace with real GIS later)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ZoneInfo:
    zone: str
    zoneNumber: int
    labelDescription: str | None
    schemeName: str
    schemeNumber: str
    lga: str
    gazettalDate: int

    def to_dict(self) -> dict:
        return asdict(self)


# Test sites the user will ask about from the chatbot
_DUMMY_SITES: list[dict] = [
    {
        "name": "22-24 Lowood Road, Mount Barker",
        "lat": -34.63000,
        "lng": 117.66700,
        "address_hints": ("lowood", "mount barker"),
        "zone": ZoneInfo(
            zone="Residential",
            zoneNumber=1,
            labelDescription=None,
            schemeName="PLANTAGENET",
            schemeNumber="5",
            lga="Shire of Plantagenet",
            gazettalDate=1613520000000,
        ),
    },
    {
        "name": "Porongurup",
        "lat": -34.66670,
        "lng": 117.86670,
        "address_hints": ("porongurup",),
        "zone": ZoneInfo(
            zone="Environmental conservation reserve",
            zoneNumber=572,
            labelDescription=None,
            schemeName="PLANTAGENET",
            schemeNumber="5",
            lga="Shire of Plantagenet",
            gazettalDate=1613520000000,
        ),
    },
]

# How close coords must be to count as the same dummy site (~100 m-ish)
_COORD_TOLERANCE = 0.002


def lookup_zone(
    *,
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> ZoneInfo | None:
    """Return dummy zone for known test locations; None if unknown."""
    if lat is not None and lng is not None:
        for site in _DUMMY_SITES:
            if (
                abs(lat - site["lat"]) <= _COORD_TOLERANCE
                and abs(lng - site["lng"]) <= _COORD_TOLERANCE
            ):
                return site["zone"]

    if address:
        lower = address.lower()
        for site in _DUMMY_SITES:
            hints: tuple[str, ...] = site["address_hints"]
            if all(h in lower for h in hints) or (
                len(hints) == 1 and hints[0] in lower
            ):
                return site["zone"]

    return None
