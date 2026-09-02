"""WebSocket message protocol shared with the Next.js client."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc: str
    clause: str | None = None
    quote: str | None = None
    page: str | None = None
    url: str | None = None
    topic: str | None = None
    location: str | None = None  # e.g. "Part B · page 42"


class ZoneInfo(BaseModel):
    zone: str
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


ClientEvent = Annotated[SessionHello | ChatSend, Field(discriminator="type")]


class SessionReady(BaseModel):
    type: Literal["session.ready"] = "session.ready"
    sessionId: str


class ChatAssistant(BaseModel):
    type: Literal["chat.assistant"] = "chat.assistant"
    sessionId: str
    content: str
    citations: list[Citation] | None = None
    zone: ZoneInfo | None = None


class ChatError(BaseModel):
    type: Literal["chat.error"] = "chat.error"
    sessionId: str | None = None
    message: str
