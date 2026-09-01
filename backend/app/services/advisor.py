"""Planning advisor: dummy GIS zone + retrieve policy clauses + reply."""

from __future__ import annotations

import logging

from app.schemas.messages import ChatAssistant, Citation, ZoneInfo as ZoneSchema
from app.services.embeddings import embed_text
from app.services.gis_dummy import ZoneInfo
from app.services.llm import generate_answer
from app.services.retriever import search_policies
from app.services.session_store import SessionContext

logger = logging.getLogger(__name__)


def _location_line(ctx: SessionContext | None) -> str:
    if ctx and ctx.address:
        coords = ""
        if ctx.lat is not None and ctx.lng is not None:
            coords = f" ({ctx.lat:.5f}, {ctx.lng:.5f})"
        return f"Using property: **{ctx.address}**{coords}"
    return "No property address is set for this session."


def _zone_line(zone: ZoneInfo | None) -> str | None:
    if not zone:
        return None
    lga = zone.schemeName or zone.lga or "PLANTAGENET"
    return f"Zoning: **{zone.zone}** (LGA: {lga})"


def _zone_schema(zone: ZoneInfo | None) -> ZoneSchema | None:
    if not zone:
        return None
    return ZoneSchema(**zone.to_dict())


def build_welcome_message(
    *,
    session_id: str,
    ctx: SessionContext | None,
) -> ChatAssistant:
    location = _location_line(ctx)
    zone = ctx.zone if ctx else None
    zone_line = _zone_line(zone)
    address = ctx.address if ctx and ctx.address else "your property"

    parts = [location, ""]
    if zone_line:
        parts.extend([zone_line, ""])
    else:
        parts.extend(
            [
                "Zoning: unknown for this pin (dummy GIS only covers two test sites).",
                "",
            ]
        )
    parts.extend(
        [
            f"Welcome — I’m the **Plantagenet Planning Advisor**.",
            "",
            f"I’ve saved **{address}** for this chat. Ask about sheds, fences, "
            "dwellings, setbacks, or zoning for this site.",
            "",
            "Guidance only — not a formal planning decision.",
        ]
    )
    return ChatAssistant(
        sessionId=session_id,
        content="\n".join(parts),
        zone=_zone_schema(zone),
    )


def build_advisor_reply(
    *,
    session_id: str,
    prompt: str,
    ctx: SessionContext | None,
) -> ChatAssistant:
    address = ctx.address if ctx else None
    zone = ctx.zone if ctx else None
    zone_name = zone.zone if zone else None

    try:
        search_text = prompt
        if zone_name:
            search_text = f"{prompt}\nProperty zone: {zone_name}"
        logger.info(
            "RAG ask session=%s zone=%s q=%r",
            session_id,
            zone_name or "unknown",
            prompt[:120],
        )
        embedding = embed_text(search_text)
        hits = search_policies(embedding, match_count=5)
        content = generate_answer(
            question=prompt,
            address=address,
            zone_name=zone_name,
            clauses=hits,
        )
        # Keep zone line visible at the top like your sample replies
        zone_line = _zone_line(zone)
        location = _location_line(ctx)
        if zone_line and not content.startswith("Using property:"):
            content = f"{location}\n\n{zone_line}\n\n{content}"
        elif zone_line and "Zoning:" not in content:
            # Insert zoning after first paragraph
            bits = content.split("\n\n", 1)
            if len(bits) == 2:
                content = f"{bits[0]}\n\n{zone_line}\n\n{bits[1]}"
            else:
                content = f"{content}\n\n{zone_line}"
        citations = _to_citations(hits)
    except Exception:
        logger.exception("RAG reply failed")
        parts = [_location_line(ctx), ""]
        zone_line = _zone_line(zone)
        if zone_line:
            parts.extend([zone_line, ""])
        parts.extend(
            [
                "Sorry — I could not search the policy database right now. "
                "Check backend Supabase settings and try again.",
                "",
                "*Guidance only — not a formal planning decision.*",
            ]
        )
        content = "\n".join(parts)
        citations = None

    return ChatAssistant(
        sessionId=session_id,
        content=content,
        citations=citations,
        zone=_zone_schema(zone),
    )


def _to_citations(hits: list[dict]) -> list[Citation] | None:
    if not hits:
        return None

    # Public landing pages for official sources (open in new tab from the UI)
    source_urls = {
        "R-Codes-Vol1-2026": (
            "https://www.wa.gov.au/government/document-collections/state-planning-policy-73-"
            "residential-design-codes"
        ),
        "LPS5": "https://www.plantagenet.wa.gov.au/council/publications-documents/",
        "LPP5": "https://www.plantagenet.wa.gov.au/council/publications-documents/",
        "TPS3-POL20": "https://www.plantagenet.wa.gov.au/council/publications-documents/",
        "POL5-RELOC": "https://www.plantagenet.wa.gov.au/council/publications-documents/",
    }

    citations: list[Citation] = []
    for row in hits:
        quote = (row.get("document") or "").strip()
        if len(quote) > 180:
            quote = quote[:177] + "..."
        source = str(row.get("source_document") or "policy")
        page = row.get("page")
        page_s = str(page).strip() if page not in (None, "", "N/A") else None
        citations.append(
            Citation(
                doc=source,
                clause=str(row.get("id") or row.get("topic") or ""),
                quote=quote or None,
                page=page_s,
                url=source_urls.get(source),
                topic=(str(row.get("topic")).strip() if row.get("topic") else None),
            )
        )
    return citations
