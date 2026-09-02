"""Planning advisor: dummy GIS zone + retrieve policy clauses + reply."""

from __future__ import annotations

import logging

from app.config import get_settings
from app.schemas.messages import ChatAssistant, Citation, ZoneInfo as ZoneSchema
from app.services.embeddings import embed_text
from app.services.gis_dummy import ZoneInfo
from app.services.llm import generate_answer, suggest_followup_query
from app.services.retriever import search_policies
from app.services.session_store import SessionContext
from app.services.source_links import citation_for_source

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
    settings = get_settings()

    try:
        search_text = prompt
        if zone_name:
            search_text = f"{prompt}\nProperty zone: {zone_name}"
        logger.info(
            "RAG ask session=%s zone=%s multi_hop=%s q=%r",
            session_id,
            zone_name or "unknown",
            settings.multi_hop,
            prompt[:120],
        )

        hop1_count = settings.multi_hop_match_count
        embedding = embed_text(search_text)
        hop1 = search_policies(embedding, match_count=hop1_count)
        hits = list(hop1)

        if settings.multi_hop:
            followup = suggest_followup_query(
                question=prompt,
                first_hits=hop1,
                zone_name=zone_name,
            )
            if followup:
                logger.info("RAG hop2 query=%r", followup[:160])
                hop2_embed = embed_text(followup)
                hop2 = search_policies(hop2_embed, match_count=hop1_count)
                hits = _merge_hits(
                    hop1,
                    hop2,
                    limit=settings.multi_hop_final_count,
                )
                logger.info(
                    "RAG multi-hop merged=%s (hop1=%s hop2=%s)",
                    len(hits),
                    len(hop1),
                    len(hop2),
                )
            else:
                logger.info("RAG multi-hop skipped (no useful follow-up)")

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


def _merge_hits(
    hop1: list[dict],
    hop2: list[dict],
    *,
    limit: int,
) -> list[dict]:
    """Merge two retrieve lists by id, keeping the higher similarity score."""
    by_id: dict[str, dict] = {}
    for row in hop1 + hop2:
        rid = str(row.get("id") or "").strip()
        if not rid:
            continue
        prev = by_id.get(rid)
        if prev is None:
            by_id[rid] = row
            continue
        prev_sim = float(prev.get("similarity") or 0.0)
        new_sim = float(row.get("similarity") or 0.0)
        if new_sim > prev_sim:
            by_id[rid] = row

    merged = list(by_id.values())
    merged.sort(key=lambda r: float(r.get("similarity") or 0.0), reverse=True)
    return merged[: max(limit, 1)]


def _to_citations(hits: list[dict]) -> list[Citation] | None:
    if not hits:
        return None

    citations: list[Citation] = []
    for row in hits:
        quote = (row.get("document") or "").strip()
        if len(quote) > 180:
            quote = quote[:177] + "..."

        source_key = str(row.get("source_document") or "policy")
        meta = citation_for_source(source_key)
        title = meta["title"]
        url = meta.get("url")

        page = row.get("page")
        page_s = str(page).strip() if page not in (None, "", "N/A", "0") else None
        section = str(row.get("section") or "").strip()
        subsection = str(row.get("subsection") or "").strip()
        item_ref = str(row.get("item_ref") or "").strip()
        topic = str(row.get("topic") or "").strip() or None

        where_bits: list[str] = []
        if section and section.upper() not in {"N/A", "NA"}:
            where_bits.append(section)
        if subsection and subsection.upper() not in {"N/A", "NA"}:
            where_bits.append(subsection)
        if item_ref and item_ref.upper() not in {"N/A", "NA"}:
            where_bits.append(f"ref {item_ref}")
        if page_s:
            where_bits.append(f"page {page_s}")

        location = " · ".join(where_bits) if where_bits else None
        clause_id = str(row.get("id") or "").strip() or None

        citations.append(
            Citation(
                doc=title,
                clause=clause_id,
                quote=quote or None,
                page=page_s,
                url=url,
                topic=topic,
                location=location,
            )
        )
    return citations
