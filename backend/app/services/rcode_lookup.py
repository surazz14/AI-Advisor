"""R-Code density coding from the WA SLIP layer
"Local Planning Scheme - R Codes (DPLH-070)":
https://public-services.slip.wa.gov.au/public/rest/services/
SLIP_Public_Services/Property_and_Planning/MapServer/111

Field ``rcode_no`` holds values such as "R10", "R2.5" or a dual code like
"R10/17.5" (base code / higher code available when the scheme's
conditions are met). Land that is not coded for housing (most rural land)
returns no feature, which simply means no R-Code applies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_RCODE_QUERY_URL = (
    "https://public-services.slip.wa.gov.au/public/rest/services/"
    "SLIP_Public_Services/Property_and_Planning/MapServer/111/query"
)
_TIMEOUT_SECONDS = 6.0

_RCODE_RE = re.compile(r"^R?\s*(\d+(?:\.\d+)?)\s*(?:/\s*R?\s*(\d+(?:\.\d+)?))?$", re.IGNORECASE)


@dataclass
class RCodeInfo:
    code: str  # as published, e.g. "R10/17.5"
    base: str  # e.g. "R10"
    alternative: str | None = None  # e.g. "R17.5" for a dual code

    @property
    def is_dual(self) -> bool:
        return self.alternative is not None

    def describe(self) -> str:
        """Short human label, e.g. 'R10/17.5 (R10 base; R17.5 if scheme conditions are met)'."""
        if self.alternative:
            return (
                f"{self.code} ({self.base} base; {self.alternative} "
                "if scheme conditions are met)"
            )
        return self.code


def parse_rcode(raw: str | None) -> RCodeInfo | None:
    """Parse 'R10', 'R2.5/20', 'R10/R17.5' into an RCodeInfo."""
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    match = _RCODE_RE.match(text)
    if not match:
        return None
    base = f"R{match.group(1)}"
    alt = f"R{match.group(2)}" if match.group(2) else None
    code = f"{base}/{alt[1:]}" if alt else base
    return RCodeInfo(code=code, base=base, alternative=alt)


async def get_rcode(lat: float, lng: float) -> RCodeInfo | None:
    """Return the R-Code at (lat, lng), or None if uncoded / lookup failed."""
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "rcode_no,scheme_nam",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.get(_RCODE_QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("R-Code lookup failed for (lat=%s, lng=%s)", lat, lng)
        return None

    if data.get("error"):
        logger.error("R-Code lookup returned an error: %s", data["error"])
        return None

    features = data.get("features") or []
    if not features:
        logger.info("R-Code lookup: no R-Code at (lat=%s, lng=%s)", lat, lng)
        return None

    raw = (features[0].get("attributes") or {}).get("rcode_no")
    info = parse_rcode(raw)
    if info is None:
        logger.warning("R-Code lookup: could not parse rcode_no=%r", raw)
        return None
    logger.info("R-Code lookup ok: %s at (lat=%s, lng=%s)", info.code, lat, lng)
    return info
