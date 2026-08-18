"""WebSocket message protocol shared with the Next.js client."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc: str
    clause: str | None = None
    quote: str | None = None


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


class ChatError(BaseModel):
    type: Literal["chat.error"] = "chat.error"
    sessionId: str | None = None
    message: str
