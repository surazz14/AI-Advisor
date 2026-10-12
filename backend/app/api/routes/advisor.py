"""REST endpoint that accepts the address form + question from the frontend
and returns an advisor reply (same logic used by the /ws/chat socket)."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.messages import AdvisorAskRequest, ChatAssistant
from app.services.advisor import build_advisor_reply
from app.services.property_context import refresh_property_facts
from app.services.session_store import session_store

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


@router.post("/ask", response_model=ChatAssistant)
async def ask_advisor(payload: AdvisorAskRequest) -> ChatAssistant:
    address = payload.address.strip()
    question = payload.question.strip()

    if not address:
        raise HTTPException(status_code=422, detail="address is required.")
    if not question:
        raise HTTPException(status_code=422, detail="question is required.")

    # REST calls don't carry a socket-scoped session id, so generate one if
    # the frontend doesn't supply one (e.g. a fresh session).
    session_id = payload.sessionId or uuid.uuid4().hex

    ctx = session_store.upsert(
        session_id,
        address=address,
        lat=payload.lat,
        lng=payload.lng,
        land_ids=payload.lot_ids,
    )
    _zone, rejection = await refresh_property_facts(
        session_id,
        address=address,
        lat=payload.lat,
        lng=payload.lng,
        land_ids=payload.lot_ids,
    )
    if rejection:
        raise HTTPException(status_code=422, detail=rejection)

    ctx = session_store.get(session_id) or ctx

    session_store.append_turn(session_id, "user", question)

    # Heavy embed/retrieve/LLM work off the event loop (same as /ws/chat).
    reply = await asyncio.to_thread(
        build_advisor_reply,
        session_id=session_id,
        prompt=question,
        ctx=ctx,
    )
    session_store.append_turn(session_id, "assistant", reply.content)

    return reply
