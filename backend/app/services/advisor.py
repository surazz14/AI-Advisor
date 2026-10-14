"""Planning advisor: live GIS zone + retrieve policy clauses + reply."""

from __future__ import annotations

import logging

from app.config import get_settings
from app.schemas.messages import (
    ChatAssistant,
    Citation,
    HeritageListing,
    ZoneInfo as ZoneSchema,
)
from app.services.bushfire_lookup import BushfireStatus, bushfire_status
from app.services.embeddings import embed_text
from app.services.llm import generate_answer, suggest_followup_query
from app.services.lot_lookup import format_lot_area
from app.services.retriever import search_policies
from app.services.session_store import SessionContext
from app.services.source_links import citation_for_source
from app.services.zone_lookup import ZoneInfo

logger = logging.getLogger(__name__)


def _location_line(ctx: SessionContext | None) -> str:
    if ctx and ctx.address:
        coords = ""
        if ctx.lat is not None and ctx.lng is not None:
            coords = f" ({ctx.lat:.5f}, {ctx.lng:.5f})"
        return f"Using property: **{ctx.address}**{coords}"
    return "No property address is set for this session."


def _zone_line(zone: ZoneInfo | None) -> str | None:
    if not zone or not zone.zone:
        return None
    lga = zone.schemeName or zone.lga or "PLANTAGENET"
    return f"Zoning: **{zone.zone}** (LGA: {lga})"


def _bushfire(ctx: SessionContext | None) -> BushfireStatus | None:
    """Lot-based result from the property lookup; the pin only as a fallback."""
    if ctx is None:
        return None
    if ctx.parcel_checked and ctx.bushfire is not None:
        return ctx.bushfire
    return bushfire_status(ctx.lat, ctx.lng)


def _bushfire_line(status: BushfireStatus | None) -> str | None:
    if status is None:
        return None
    if not status.inside:
        return "Bushfire-prone area: **No** (outside the mapped Bush Fire Prone Area)"
    when = f", designated {status.latest_date}" if status.latest_date else ""
    part = ""
    if status.partial and status.lot_share is not None:
        part = f" — about {max(round(status.lot_share * 100), 1)}% of the lot is in the mapped area"
    return (
        f"Bushfire-prone area: **Yes**{part}"
        f"{when} (OBRM map — extra planning and building rules may apply; not a BAL rating)"
    )


def _lot_area(ctx: SessionContext | None) -> float | None:
    return ctx.lot_area_m2 if ctx else None


def _lot_count(ctx: SessionContext | None) -> int | None:
    """Lots combined into the site area (None when it is a single lot)."""
    if ctx and ctx.lot_area_m2 and ctx.lot_count > 1:
        return ctx.lot_count
    return None


def _lot_line(ctx: SessionContext | None) -> str | None:
    label = format_lot_area(_lot_area(ctx))
    if not label:
        return None
    lots = _lot_count(ctx)
    if lots:
        return f"Lot area: **{label}** across {lots} lots at this address (approx., from Landgate cadastre)"
    return f"Lot area: **{label}** (approx., from Landgate cadastre)"


def _rcode_code(ctx: SessionContext | None) -> str | None:
    return ctx.rcode.code if ctx and ctx.rcode else None


def _rcode_line(ctx: SessionContext | None) -> str | None:
    if not ctx or not ctx.rcode:
        return None
    return f"R-Code: **{ctx.rcode.describe()}**"


def _heritage_lines(
    ctx: SessionContext | None, *, include_none: bool = False
) -> list[str]:
    """Heritage facts for the header. 'None found' only when include_none."""
    if not ctx or not ctx.parcel_checked:
        return []
    info = ctx.heritage
    if info is None:
        return ["Heritage: **could not be checked** (map service unavailable) — confirm with the Shire"]

    lines: list[str] = []
    # Survey entries duplicate most statutory listings — only show extra ones
    statutory_nos = {m.place_no for m in info.statutory if m.place_no}
    listed = info.statutory + [
        m for m in info.survey_only if m.place_no not in statutory_nos
    ]
    if listed:
        lines.append("Heritage: **" + "; ".join(m.describe() for m in listed) + "**")
    if info.aboriginal:
        lines.append(
            "Aboriginal heritage: **"
            + "; ".join(m.describe() for m in info.aboriginal)
            + "**"
        )
    if not lines and include_none:
        if info.checked_with != "lot":
            where = "at this address point"
        elif ctx.lot_count > 1:
            where = "on these lots"
        else:
            where = "on this lot"
        lines.append(f"Heritage: no listing found {where}")
    if info.incomplete and lines:
        lines[-1] += " (some heritage maps were unavailable)"
    return lines


def _heritage_schema(ctx: SessionContext | None) -> list[HeritageListing] | None:
    if not ctx or not ctx.heritage:
        return None
    return [
        HeritageListing(
            kind=m.kind,
            label=m.label,
            placeName=m.place_name,
            placeNo=m.place_no,
            url=m.url,
        )
        for m in ctx.heritage.matches
    ]


def _facts_block(
    zone: ZoneInfo | None,
    ctx: SessionContext | None,
    bushfire: BushfireStatus | None = None,
) -> str | None:
    lines = [
        line
        for line in (
            _zone_line(zone),
            _bushfire_line(bushfire),
            _lot_line(ctx),
            _rcode_line(ctx),
        )
        if line
    ]
    lines.extend(_heritage_lines(ctx))
    return "\n".join(lines) if lines else None


def _zone_schema(zone: ZoneInfo | None) -> ZoneSchema | None:
    if not zone or not zone.zone:
        return None
    return ZoneSchema(**zone.to_dict())


def build_welcome_message(
    *,
    session_id: str,
    ctx: SessionContext | None,
) -> ChatAssistant:
    location = _location_line(ctx)
    zone = ctx.zone if ctx else None
    bushfire = _bushfire(ctx)
    address = ctx.address if ctx and ctx.address else "your property"

    parts = [location, ""]
    zone_line = _zone_line(zone)
    extra_lines = [line for line in (_lot_line(ctx), _rcode_line(ctx)) if line]
    extra_lines.extend(_heritage_lines(ctx, include_none=True))
    if zone_line:
        parts.extend([zone_line, *extra_lines, ""])
    else:
        parts.extend(
            [
                "Zoning: unknown for this pin "
                "(need map coordinates for live zone lookup, or the point is unmapped).",
                *extra_lines,
                "",
            ]
        )
    bushfire_line = _bushfire_line(bushfire)
    if bushfire_line:
        parts.extend([bushfire_line, ""])
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
        lotAreaM2=_lot_area(ctx),
        lotCount=_lot_count(ctx),
        rCode=_rcode_code(ctx),
        heritage=_heritage_schema(ctx),
        bushfireProne=bushfire.inside if bushfire else None,
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
    bushfire = _bushfire(ctx)
    settings = get_settings()

    try:
        search_text = prompt
        if zone_name:
            search_text = f"{prompt}\nProperty zone: {zone_name}"
        if bushfire and bushfire.inside:
            search_text += (
                "\nProperty is inside a designated Bush Fire Prone Area. "
                "Apply SPP 3.7 bushfire requirements."
            )
        lot_area_m2 = _lot_area(ctx)
        if lot_area_m2:
            search_text = f"{search_text}\nLot area: {lot_area_m2:.0f} m2"
        rcode = ctx.rcode if ctx else None
        if rcode:
            search_text = f"{search_text}\nR-Code density: {rcode.base}"
        heritage = ctx.heritage if ctx else None
        if heritage and heritage.statutory:
            search_text = f"{search_text}\nHeritage listed place"
        logger.info(
            "RAG ask session=%s zone=%s multi_hop=%s q=%r",
            session_id,
            zone_name or "unknown",
            settings.multi_hop,
            prompt[:120],
        )

        hop1_count = settings.multi_hop_match_count
        embedding = embed_text(search_text)
        hop1 = search_policies(
            embedding,
            match_count=hop1_count,
            zone_name=zone_name,
            query_text=prompt,
        )
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
                hop2 = search_policies(
                    hop2_embed,
                    match_count=hop1_count,
                    zone_name=zone_name,
                    query_text=followup,
                )
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

        bushfire_note = None
        if bushfire and bushfire.inside:
            where = (
                f"About {max(round(bushfire.lot_share * 100), 1)}% of the lot is"
                if bushfire.partial and bushfire.lot_share is not None
                else "The lot is"
            )
            bushfire_note = (
                f"{where} inside a designated Bush Fire Prone Area on the "
                "Plantagenet OBRM map, so the property counts as bushfire prone. "
                "Say that SPP 3.7 may apply. Do not invent a BAL rating."
            )
        elif bushfire and not bushfire.inside:
            bushfire_note = (
                "The property is outside the mapped Bush Fire Prone Area. "
                "Do not treat the site as bushfire-prone unless the clauses say otherwise."
            )
        content = generate_answer(
            question=prompt,
            address=address,
            zone_name=zone_name,
            clauses=hits,
            bushfire_note=bushfire_note,
            lot_area_m2=lot_area_m2,
            lot_count=_lot_count(ctx),
            rcode=rcode,
            heritage=heritage,
            heritage_checked=bool(ctx and ctx.parcel_checked),
        )
        # Keep zone, bushfire + lot facts visible at the top like your sample replies
        facts = _facts_block(zone, ctx, bushfire)
        location = _location_line(ctx)
        if facts and not content.startswith("Using property:"):
            content = f"{location}\n\n{facts}\n\n{content}"
        elif facts and "Zoning:" not in content and "Bushfire-prone area:" not in content:
            # Insert facts after first paragraph
            bits = content.split("\n\n", 1)
            if len(bits) == 2:
                content = f"{bits[0]}\n\n{facts}\n\n{bits[1]}"
            else:
                content = f"{content}\n\n{facts}"
        citations = _to_citations(hits)
    except Exception as exc:
        logger.exception("RAG reply failed")
        parts = [_location_line(ctx), ""]
        facts = _facts_block(zone, ctx, bushfire)
        if facts:
            parts.extend([facts, ""])
        hint = str(exc).strip().split("\n")[0][:160]
        if "SUPABASE" in hint.upper() or "supabase" in hint.lower():
            user_msg = (
                "Sorry — I could not search the policy database right now. "
                "Check backend Supabase settings and try again."
            )
        else:
            user_msg = (
                "Sorry — I could not finish that answer right now "
                f"({type(exc).__name__}: {hint or 'see API logs'})."
            )
        parts.extend(
            [
                user_msg,
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
        lotAreaM2=_lot_area(ctx),
        lotCount=_lot_count(ctx),
        rCode=_rcode_code(ctx),
        heritage=_heritage_schema(ctx),
        bushfireProne=bushfire.inside if bushfire else None,
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
