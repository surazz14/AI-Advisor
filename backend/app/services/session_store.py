"""In-memory session context until a real store exists.

Zoning comes from the live SLIP lookup (see zone_lookup.resolve_zone),
applied by the WebSocket / REST handlers — not from a dummy GIS table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.heritage_lookup import HeritageInfo
from app.services.rcode_lookup import RCodeInfo
from app.services.zone_lookup import ZoneInfo


@dataclass
class SessionContext:
    session_id: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    # Landgate land_ids of every lot at the address picked in the search
    land_ids: tuple[int, ...] | None = None
    zone: ZoneInfo | None = None
    # Approximate lot / site area from Landgate cadastre (None = unknown)
    lot_area_m2: float | None = None
    # How many cadastral lots lot_area_m2 covers
    lot_count: int = 1
    # R-Code density coding (None = no R-Code applies, or unknown)
    rcode: RCodeInfo | None = None
    # Heritage listings on the lot (None = lookup failed / unknown)
    heritage: HeritageInfo | None = None
    # True once lot area + R-Code have been looked up for this location
    parcel_checked: bool = False
    welcome_sent: bool = False
    history: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def upsert(
        self,
        session_id: str,
        *,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        land_ids: list[int] | None = None,
    ) -> SessionContext:
        ids = tuple(sorted(set(land_ids))) if land_ids else None
        existing = self._sessions.get(session_id)
        if existing is None:
            ctx = SessionContext(
                session_id=session_id,
                address=address,
                lat=lat,
                lng=lng,
                land_ids=ids,
                zone=None,
            )
            self._sessions[session_id] = ctx
            return ctx

        if address is not None and address != existing.address:
            existing.address = address
            existing.welcome_sent = False
            # Location changed — clear stale zone/lot until live lookup refreshes it
            existing.zone = None
            self._reset_lot(existing)
        elif address is not None:
            existing.address = address

        if lat is not None and existing.lat != lat:
            existing.lat = lat
            existing.zone = None
            self._reset_lot(existing)
        elif lat is not None:
            existing.lat = lat

        if lng is not None and existing.lng != lng:
            existing.lng = lng
            existing.zone = None
            self._reset_lot(existing)
        elif lng is not None:
            existing.lng = lng

        if ids is not None and existing.land_ids != ids:
            existing.land_ids = ids
            existing.zone = None
            self._reset_lot(existing)
        elif ids is None and (address is not None or lat is not None):
            # New location without Landgate lots (e.g. OpenStreetMap pick)
            if existing.land_ids is not None:
                existing.land_ids = None
                self._reset_lot(existing)

        return existing

    @staticmethod
    def _reset_lot(ctx: SessionContext) -> None:
        ctx.lot_area_m2 = None
        ctx.lot_count = 1
        ctx.rcode = None
        ctx.heritage = None
        ctx.parcel_checked = False

    def set_parcel_facts(
        self,
        session_id: str,
        *,
        lot_area_m2: float | None,
        rcode: RCodeInfo | None,
        heritage: HeritageInfo | None = None,
        lot_count: int = 1,
    ) -> None:
        ctx = self.get(session_id)
        if ctx is not None:
            ctx.lot_area_m2 = lot_area_m2
            ctx.lot_count = lot_count
            ctx.rcode = rcode
            ctx.heritage = heritage
            ctx.parcel_checked = True

    def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    def set_zone(self, session_id: str, zone: ZoneInfo | None) -> None:
        ctx = self.get(session_id)
        if ctx is not None:
            ctx.zone = zone

    def clear_location(self, session_id: str) -> None:
        """Drop address / coords / zone so chat cannot continue for a rejected pin."""
        ctx = self.get(session_id)
        if ctx is None:
            return
        ctx.address = None
        ctx.lat = None
        ctx.lng = None
        ctx.land_ids = None
        ctx.zone = None
        self._reset_lot(ctx)
        ctx.welcome_sent = False

    def append_turn(self, session_id: str, role: str, content: str) -> None:
        ctx = self.get(session_id)
        if ctx is None:
            ctx = self.upsert(session_id)
        ctx.history.append({"role": role, "content": content})
        if len(ctx.history) > 40:
            ctx.history = ctx.history[-40:]


session_store = SessionStore()
