"""REST endpoint that accepts the address form + question from the frontend
and returns an advisor reply (same logic used by the /ws/chat socket)."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.messages import AdvisorAskRequest, ChatAssistant
from app.services.advisor import build_advisor_reply
from app.services.session_store import session_store
from app.services.zone_lookup import get_zone_info

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
    )
    if payload.lat is not None and payload.lng is not None and ctx.zone is None:
        zone = await get_zone_info(payload.lat, payload.lng)
        session_store.set_zone(session_id, zone)
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
