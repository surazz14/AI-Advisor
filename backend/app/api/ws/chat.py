from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError

from app.schemas.messages import (
    ChatError,
    ChatSend,
    ClientEvent,
    SessionHello,
    SessionReady,
)
from app.services.advisor import build_advisor_reply, build_welcome_message
from app.services.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

_client_adapter = TypeAdapter(ClientEvent)


async def _send_json(websocket: WebSocket, payload: object) -> None:
    if hasattr(payload, "model_dump"):
        await websocket.send_json(payload.model_dump(exclude_none=True))
    else:
        await websocket.send_json(payload)


@router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket connected from %s", websocket.client)

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                event = _client_adapter.validate_python(raw)
            except ValidationError as exc:
                await _send_json(
                    websocket,
                    ChatError(
                        message=f"Invalid client message: {exc.errors()[0].get('msg', 'validation error')}",
                    ),
                )
                continue

            if isinstance(event, SessionHello):
                ctx = session_store.upsert(
                    event.sessionId,
                    address=event.address,
                    lat=event.lat,
                    lng=event.lng,
                )
                await _send_json(
                    websocket,
                    SessionReady(sessionId=event.sessionId),
                )
                # Default welcome from backend when address is first set / changed
                if event.address and not ctx.welcome_sent:
                    welcome = build_welcome_message(
                        session_id=event.sessionId,
                        ctx=ctx,
                    )
                    session_store.append_turn(
                        event.sessionId,
                        "assistant",
                        welcome.content,
                    )
                    ctx.welcome_sent = True
                    await _send_json(websocket, welcome)
                continue

            if isinstance(event, ChatSend):
                content = event.content.strip()
                if not content:
                    await _send_json(
                        websocket,
                        ChatError(
                            sessionId=event.sessionId,
                            message="Message content cannot be empty.",
                        ),
                    )
                    continue

                ctx = session_store.upsert(
                    event.sessionId,
                    address=event.address,
                    lat=event.lat,
                    lng=event.lng,
                )
                session_store.append_turn(event.sessionId, "user", content)

                reply = build_advisor_reply(
                    session_id=event.sessionId,
                    prompt=content,
                    ctx=ctx,
                )
                session_store.append_turn(
                    event.sessionId,
                    "assistant",
                    reply.content,
                )
                await _send_json(websocket, reply)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("Unexpected WebSocket error")
        try:
            await _send_json(
                websocket,
                ChatError(message="Internal chat server error."),
            )
        except Exception:
            pass
