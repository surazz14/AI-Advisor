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


class HeritageListing(BaseModel):
    kind: str  # state_register | heritage_list | heritage_area | local_heritage_survey | aboriginal_*
    label: str
    placeName: str | None = None
    placeNo: str | None = None
    url: str | None = None


class ZoneInfo(BaseModel):
    zone: str
    zoneNumber: int | None = None
    labelDescription: str | None = None
    schemeName: str | None = None
    schemeNumber: str | None = None
    lga: str | None = None
    gazettalDate: int | None = None


class _LotRefs(BaseModel):
    """Landgate lot ids picked in the address search (one address can span several lots)."""

    landIds: list[int] | None = None
    # Single-lot form sent by older browser sessions
    landId: int | None = None

    @property
    def lot_ids(self) -> list[int] | None:
        if self.landIds:
            return list(self.landIds)
        if self.landId is not None:
            return [self.landId]
        return None


class SessionHello(_LotRefs):
    type: Literal["session.hello"]
    sessionId: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None


class ChatSend(_LotRefs):
    type: Literal["chat.send"]
    sessionId: str
    content: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None


class AdvisorAskRequest(_LotRefs):
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


class TrustScore(BaseModel):
    """How much of an answer is backed by retrieved facts (see services/trust.py)."""

    score: int  # 0–100
    level: Literal["high", "medium", "low"]
    citedStatements: int
    totalStatements: int
    supportedFigures: int
    totalFigures: int
    unsupportedFigures: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class ChatAssistant(BaseModel):
    type: Literal["chat.assistant"] = "chat.assistant"
    sessionId: str
    content: str
    # Which client event this answers, so a pending question never mistakes a
    # reconnect welcome (session.hello) for its reply.
    replyTo: Literal["session.hello", "chat.send"] | None = None
    citations: list[Citation] | None = None
    zone: ZoneInfo | None = None
    # Approximate lot / site area (m²) from Landgate cadastre
    lotAreaM2: float | None = None
    # Number of lots at this address that make up lotAreaM2 (omitted = 1 / unknown)
    lotCount: int | None = None
    # R-Code density coding, e.g. "R10" or dual "R10/17.5"
    rCode: str | None = None
    # Heritage listings on the lot ([] = checked, none found; omitted = unknown)
    heritage: list[HeritageListing] | None = None
    # Inside a mapped Bush Fire Prone Area (None = unknown)
    bushfireProne: bool | None = None
    # Grounding of the answer in the cited clauses (None for welcome/errors)
    trust: TrustScore | None = None


class ChatError(BaseModel):
    type: Literal["chat.error"] = "chat.error"
    sessionId: str | None = None
    message: str
