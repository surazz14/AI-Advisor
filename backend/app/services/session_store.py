from __future__ import annotations

from dataclasses import dataclass, field

from app.services.gis_dummy import ZoneInfo, lookup_zone


@dataclass
class SessionContext:
    session_id: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    zone: ZoneInfo | None = None
    welcome_sent: bool = False
    history: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    """In-memory session context until a real store exists."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def upsert(
        self,
        session_id: str,
        *,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> SessionContext:
        existing = self._sessions.get(session_id)
        if existing is None:
            ctx = SessionContext(
                session_id=session_id,
                address=address,
                lat=lat,
                lng=lng,
            )
            ctx.zone = lookup_zone(address=address, lat=lat, lng=lng)
            self._sessions[session_id] = ctx
            return ctx

        location_changed = False
        if address is not None and address != existing.address:
            existing.address = address
            existing.welcome_sent = False
            location_changed = True
        elif address is not None:
            existing.address = address
        if lat is not None:
            if existing.lat != lat:
                location_changed = True
            existing.lat = lat
        if lng is not None:
            if existing.lng != lng:
                location_changed = True
            existing.lng = lng

        if location_changed or existing.zone is None:
            existing.zone = lookup_zone(
                address=existing.address,
                lat=existing.lat,
                lng=existing.lng,
            )
        return existing

    def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    def set_zone(self, session_id: str, zone: ZoneInfo | None) -> None:
        ctx = self.get(session_id)
        if ctx is not None:
            ctx.zone = zone

    def append_turn(self, session_id: str, role: str, content: str) -> None:
        ctx = self.get(session_id)
        if ctx is None:
            ctx = self.upsert(session_id)
        ctx.history.append({"role": role, "content": content})
        if len(ctx.history) > 40:
            ctx.history = ctx.history[-40:]


session_store = SessionStore()
