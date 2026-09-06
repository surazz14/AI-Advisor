"""In-memory session context until a real store exists.

Zoning comes from the live SLIP lookup (see zone_lookup.resolve_zone),
applied by the WebSocket / REST handlers — not from a dummy GIS table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.zone_lookup import ZoneInfo


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
                zone=None,
            )
            self._sessions[session_id] = ctx
            return ctx

        if address is not None and address != existing.address:
            existing.address = address
            existing.welcome_sent = False
            # Location changed — clear stale zone until live lookup refreshes it
            existing.zone = None
        elif address is not None:
            existing.address = address

        if lat is not None and existing.lat != lat:
            existing.lat = lat
            existing.zone = None
        elif lat is not None:
            existing.lat = lat

        if lng is not None and existing.lng != lng:
            existing.lng = lng
            existing.zone = None
        elif lng is not None:
            existing.lng = lng

        return existing

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
        ctx.zone = None
        ctx.welcome_sent = False

    def append_turn(self, session_id: str, role: str, content: str) -> None:
        ctx = self.get(session_id)
        if ctx is None:
            ctx = self.upsert(session_id)
        ctx.history.append({"role": role, "content": content})
        if len(ctx.history) > 40:
            ctx.history = ctx.history[-40:]


session_store = SessionStore()
