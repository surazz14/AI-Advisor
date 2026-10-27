"""Planning advisor: live GIS zone + retrieve policy clauses + reply."""

from __future__ import annotations

import logging
import re

from app.config import get_settings
from app.schemas.messages import (
    ChatAssistant,
    Citation,
    HeritageListing,
    TrustScore,
    ZoneInfo as ZoneSchema,
)
from app.services.bushfire_lookup import BushfireStatus, bushfire_status
from app.services.embeddings import embed_text
from app.services.llm import generate_answer, suggest_followup_query
from app.services.lot_lookup import format_lot_area
from app.services.retriever import search_policies
from app.services.session_store import SessionContext
from app.services.source_links import citation_for_source
from app.services.trust import compute_trust
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


# SPP 3.7 mainly bites on habitable / vulnerable development and subdivision.
_BUSHFIRE_TOPIC = re.compile(r"\b(bush\s?fire|fire|bal|apz|asset protection)\b", re.I)
_BUSHFIRE_SENSITIVE_WORK = re.compile(
    # "house" only as a noun ("a new house"), not the verb ("would house a pump").
    r"\b((?:a|an|the|my|our|new|main|second) house|home|dwelling|granny|ancillary|extension|"
    r"addition|habitable|tourism|tourist|"
    r"chalet|b&b|bed and breakfast|holiday|caravan|camp|glamping|child ?care|day ?care|"
    r"subdivi\w*)",
    re.I,
)
# Works where the question is really about something else (water, fences, ...).
_NON_BUSHFIRE_SUBJECT = re.compile(
    r"\b(stormwater|drainage|runoff|soakwell|fence|fencing|water tank|rainwater tank|dam|pond)",
    re.I,
)


def _bushfire_relevant(prompt: str) -> bool:
    """Should bushfire policy be pulled into the search for this question?"""
    if _BUSHFIRE_TOPIC.search(prompt):
        return True
    return bool(_BUSHFIRE_SENSITIVE_WORK.search(prompt)) and not _NON_BUSHFIRE_SUBJECT.search(prompt)


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
    trust: TrustScore | None = None

    try:
        search_text = prompt
        if zone_name:
            search_text = f"{prompt}\nProperty zone: {zone_name}"
        # Only steer the search toward bushfire policy when it bears on the
        # question; otherwise SPP 3.7 clauses crowd out the relevant ones.
        if bushfire and bushfire.inside and _bushfire_relevant(prompt):
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
                "Plantagenet OBRM map. Bring up bushfire (SPP 3.7) only if the "
                "question is about bushfire or the clauses make it apply to this "
                "kind of work. Do not invent a BAL rating."
            )
        elif bushfire and not bushfire.inside:
            bushfire_note = (
                "The property is outside the mapped Bush Fire Prone Area. "
                "Do not treat the site as bushfire-prone unless the clauses say otherwise."
            )
        answer = generate_answer(
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
        # Cite only what the answer uses, and always end with the notice
        # (added here rather than left to the model).
        content, hits = _keep_cited(answer, hits)
        facts = _facts_block(zone, ctx, bushfire)
        result = compute_trust(
            content,
            cited_texts=[str(h.get("document") or "") for h in hits],
            facts_text=f"{_location_line(ctx)}\n{facts or ''}",
            question=prompt,
            extractive="Simple retrieval reply" in content,
        )
        trust = TrustScore(
            score=result.score,
            level=result.level,
            citedStatements=result.cited_statements,
            totalStatements=result.total_statements,
            supportedFigures=result.supported_figures,
            totalFigures=result.total_figures,
            unsupportedFigures=result.unsupported_figures,
            reasons=result.reasons,
        )
        if "guidance only" not in content.lower():
            content = f"{content.rstrip()}\n\n{GUIDANCE_NOTICE}"
        # Keep zone, bushfire + lot facts visible at the top like your sample replies
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
        trust=trust,
    )


GUIDANCE_NOTICE = "*Guidance only — not a formal planning decision.*"

# Citation markers the model writes: [3], [1, 4], [5-7], [5‑7] and the
# full-width 【3】 / 【3†source】 style some models emit.
_FULLWIDTH_CITE = re.compile(r"【\s*(\d+)[^】]*】")
_BRACKET_RANGE = re.compile(r"\[(\d+)\]\s*[–—‑-]\s*\[(\d+)\]")
_CITE_GROUP = re.compile(r"\[(\d+(?:\s*[,–—‑-]\s*\d+)*)\]")


def _cited_numbers(group: str) -> list[int]:
    numbers: list[int] = []
    for part in group.split(","):
        bounds = [b for b in re.split(r"\s*[–—‑-]\s*", part.strip()) if b]
        if len(bounds) == 2 and int(bounds[0]) <= int(bounds[1]) <= int(bounds[0]) + 20:
            numbers.extend(range(int(bounds[0]), int(bounds[1]) + 1))
        else:
            numbers.extend(int(b) for b in bounds)
    return numbers


def _keep_cited(content: str, hits: list[dict]) -> tuple[str, list[dict]]:
    """Keep only the clauses the answer cites, renumbered 1..n in reading order.

    The Sources panel lists citations in order, so markers are rewritten to
    match. If the answer cites nothing usable, everything is kept unchanged.
    """
    text = _FULLWIDTH_CITE.sub(r"[\1]", content)
    # Some answers cite by clause id ("[C61_0002]") — turn those into numbers.
    index_of = {str(h.get("id")): i for i, h in enumerate(hits, start=1) if h.get("id")}
    text = re.sub(
        r"\[([A-Za-z][\w.]*_[\w.]+)\]",
        lambda m: f"[{index_of[m.group(1)]}]" if m.group(1) in index_of else m.group(0),
        text,
    )
    text = _BRACKET_RANGE.sub(r"[\1-\2]", text)

    order: list[int] = []
    for match in _CITE_GROUP.finditer(text):
        for n in _cited_numbers(match.group(1)):
            if 1 <= n <= len(hits) and n not in order:
                order.append(n)
    if not order:
        return text, hits

    new_number = {old: new for new, old in enumerate(order, start=1)}

    def _renumber(match: re.Match) -> str:
        numbers = sorted(
            {new_number[n] for n in _cited_numbers(match.group(1)) if n in new_number}
        )
        return f"[{', '.join(map(str, numbers))}]" if numbers else ""

    text = _CITE_GROUP.sub(_renumber, text)
    return text, [hits[n - 1] for n in order]


def _merge_hits(
    hop1: list[dict],
    hop2: list[dict],
    *,
    limit: int,
) -> list[dict]:
    """Combine the main search with the follow-up search.

    Both lists arrive already ranked (zone fit + keyword matches). Keep hop1's
    top two-thirds in order — they answer the question directly — then fill
    the rest with hop2's best new clauses. Re-sorting by raw similarity used to
    let a generic follow-up (e.g. clause 61 exemptions) push out the key clause
    (e.g. LPP3's Rural shed limits or LPP6 for a water-tank question).
    """
    limit = max(limit, 1)
    keep_hop1 = min(len(hop1), -(-limit * 2 // 3))  # ceil(2/3 of limit)
    merged: list[dict] = []
    seen: set[str] = set()

    def _take(rows: list[dict], cap: int) -> None:
        for row in rows:
            if len(merged) >= cap:
                return
            rid = str(row.get("id") or "").strip()
            if rid and rid not in seen:
                seen.add(rid)
                merged.append(row)

    _take(hop1[:keep_hop1], limit)
    _take(hop2, limit)
    _take(hop1[keep_hop1:], limit)  # follow-up added little: top up from hop1
    return merged


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
