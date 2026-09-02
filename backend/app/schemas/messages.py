"""WebSocket message protocol shared with the Next.js client."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc: str
    clause: str | None = None
    quote: str | None = None


class ZoneDetails(BaseModel):
    """Planning zone for the session's property, from the live WA DPLH
    zone lookup (see app/services/zone_lookup.py). All fields optional --
    a lookup can partially match or fail entirely.

    Field names are camelCase (matching SessionHello/ChatSend above) so
    they line up 1:1 with src/types/socket.ts on the frontend without a
    translation layer."""

    zone: str | None = None
    zoneNumber: int | None = None
    labelDescription: str | None = None
    schemeName: str | None = None
    schemeNumber: str | None = None
    lga: str | None = None
    gazettalDate: int | None = None


class SessionHello(BaseModel):
    type: Literal["session.hello"]
    sessionId: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None


class ChatSend(BaseModel):
    type: Literal["chat.send"]
    sessionId: str
    content: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None


class AdvisorAskRequest(BaseModel):
    """REST request body for POST /api/advisor/ask."""

    sessionId: str | None = None
    address: str
    lat: float | None = None
    lng: float | None = None
    question: str


ClientEvent = Annotated[SessionHello | ChatSend, Field(discriminator="type")]


class SessionReady(BaseModel):
    type: Literal["session.ready"] = "session.ready"
    sessionId: str


class ChatAssistant(BaseModel):
    type: Literal["chat.assistant"] = "chat.assistant"
    sessionId: str
    content: str
    citations: list[Citation] | None = None
    zone: ZoneDetails | None = None


class ChatError(BaseModel):
    type: Literal["chat.error"] = "chat.error"
    sessionId: str | None = None
    message: str
