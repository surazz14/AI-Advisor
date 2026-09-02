"""Planning advisor reply service.

Stub responses for now. Later: GIS property facts + RAG over LPS No. 5 / LPPs.
"""

from __future__ import annotations

from app.schemas.messages import ChatAssistant, Citation, ZoneDetails
from app.services.session_store import SessionContext


def _location_line(ctx: SessionContext | None) -> str:
    if not (ctx and ctx.address):
        return "No property address is set for this session."

    coords = ""
    if ctx.lat is not None and ctx.lng is not None:
        coords = f" ({ctx.lat:.5f}, {ctx.lng:.5f})"
    line = f"Using property: **{ctx.address}**{coords}"

    if ctx.zone and ctx.zone.zone:
        zone_text = ctx.zone.zone
        label = ctx.zone.label_description
        if label and label.strip().lower() != zone_text.strip().lower():
            zone_text += f" — {label}"
        line += f"\n\nZoning: **{zone_text}**"
        if ctx.zone.scheme_name:
            line += f" (LGA: {ctx.zone.scheme_name})"

    return line


def _zone_schema(ctx: SessionContext | None) -> ZoneDetails | None:
    """Convert the cached ZoneInfo (internal dataclass) into the
    ZoneDetails Pydantic schema returned to clients, so callers get zone
    data as a structured field instead of having to parse it out of the
    reply text."""
    if not (ctx and ctx.zone):
        return None
    z = ctx.zone
    return ZoneDetails(
        zone=z.zone,
        zoneNumber=z.zone_number,
        labelDescription=z.label_description,
        schemeName=z.scheme_name,
        schemeNumber=z.scheme_number,
        lga=z.lga,
        gazettalDate=z.gazettal_date,
    )


def build_welcome_message(
    *,
    session_id: str,
    ctx: SessionContext | None,
) -> ChatAssistant:
    location = _location_line(ctx)
    address = ctx.address if ctx and ctx.address else "your property"
    content = (
        f"{location}\n\n"
        f"Welcome — I’m the **Plantagenet Planning Advisor** backend.\n\n"
        f"I’ve saved **{address}** for this chat. Ask about sheds, fences, "
        "dwellings, setbacks, or bushfire-related planning questions for this "
        "site in the Shire of Plantagenet.\n\n"
        "Guidance only — not a formal planning decision."
    )
    return ChatAssistant(
        sessionId=session_id,
        content=content,
        zone=_zone_schema(ctx),
    )


def build_advisor_reply(
    *,
    session_id: str,
    prompt: str,
    ctx: SessionContext | None,
) -> ChatAssistant:
    lower = prompt.lower()
    location = _location_line(ctx)

    if "fence" in lower:
        content = (
            f"{location}\n\n"
            "For fencing questions I will retrieve the relevant "
            "**Local Planning Scheme No. 5** and local planning policy clauses "
            "(RAG — coming next).\n\n"
            "Useful details: proposed height, materials, and whether it is a "
            "street or side/rear boundary.\n\n"
            "*Live reply from FastAPI stub — not a formal planning decision.*"
        )
        citations = [
            Citation(
                doc="Local Planning Scheme No. 5",
                clause="(pending retrieval)",
                quote="Fence guidance will cite the retrieved clause here.",
            )
        ]
    elif "shed" in lower or "outbuilding" in lower:
        content = (
            f"{location}\n\n"
            "Shed / outbuilding advice will be grounded in LPS No. 5 and local "
            "policy text once RAG is connected.\n\n"
            "Useful details: size (m²), wall/ridge height, and roughly where on "
            "the lot it will sit.\n\n"
            "*Live reply from FastAPI stub — not a formal planning decision.*"
        )
        citations = [
            Citation(
                doc="Local Planning Scheme No. 5",
                clause="(pending retrieval)",
            )
        ]
    elif any(w in lower for w in ("dwelling", "house", "build", "home")):
        content = (
            f"{location}\n\n"
            "Dwelling questions usually need zoning, bushfire status, and "
            "setback rules from the scheme and policies.\n\n"
            "Once GIS + RAG are connected, answers will cite exact clauses and "
            "property facts.\n\n"
            "*Live reply from FastAPI stub — not a formal planning decision.*"
        )
        citations = None
    else:
        content = (
            f"{location}\n\n"
            f"I received: “{prompt.strip()}”\n\n"
            "Ask about sheds, fences, dwellings, setbacks, or bushfire-related "
            "planning questions for this site in the Shire of Plantagenet.\n\n"
            "*Live reply from FastAPI stub — not a formal planning decision.*"
        )
        citations = None

    return ChatAssistant(
        sessionId=session_id,
        content=content,
        citations=citations,
        zone=_zone_schema(ctx),
    )
