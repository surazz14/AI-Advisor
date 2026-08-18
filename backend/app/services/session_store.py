from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionContext:
    session_id: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    welcome_sent: bool = False
    history: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    """In-memory session context until a real store / RAG pipeline exists."""

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
            self._sessions[session_id] = ctx
            return ctx

        if address is not None and address != existing.address:
            existing.address = address
            existing.welcome_sent = False
        elif address is not None:
            existing.address = address
        if lat is not None:
            existing.lat = lat
        if lng is not None:
            existing.lng = lng
        return existing

    def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    def append_turn(self, session_id: str, role: str, content: str) -> None:
        ctx = self.get(session_id)
        if ctx is None:
            ctx = self.upsert(session_id)
        ctx.history.append({"role": role, "content": content})
        # Keep a short working window for later RAG / LLM context
        if len(ctx.history) > 40:
            ctx.history = ctx.history[-40:]


session_store = SessionStore()
