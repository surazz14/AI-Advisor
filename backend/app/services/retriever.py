"""Search Supabase policy_chunks via hybrid retrieval.

1. Vector similarity (match_policy_chunks RPC)
2. Keyword / exact-term search (ilike on document/topic/source)
3. Reciprocal Rank Fusion (RRF) merge
4. Optional soft zone re-rank on applicable_zones
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)

# Longer names first so "rural residential" wins over "rural".
_CANONICAL_ZONES: tuple[str, ...] = (
    "rural residential",
    "rural smallholdings",
    "rural village",
    "urban development",
    "service commercial",
    "general industry",
    "strategic industry",
    "mixed use",
    "special use",
    "residential",
    "commercial",
    "tourism",
    "rural",
)

_ZONE_BOOST = 0.32
_ALL_ZONES_BOOST = 0.10
_MISMATCH_PENALTY = -0.18
_CANDIDATE_MULTIPLIER = 3
_CANDIDATE_CAP = 40
_RRF_K = 60

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "for",
        "to",
        "of",
        "in",
        "on",
        "at",
        "is",
        "are",
        "be",
        "can",
        "i",
        "my",
        "we",
        "you",
        "do",
        "does",
        "need",
        "want",
        "have",
        "has",
        "with",
        "from",
        "this",
        "that",
        "what",
        "when",
        "where",
        "how",
        "about",
        "please",
        "property",
        "zone",
        "zoning",
        "clause",
        "policy",
        "planning",
        "approval",
        "building",
        "local",
        "shire",
        "says",
        "tell",
        "does",
    }
)

# Exact-ish planning terms worth forcing into keyword search
_POLICY_TERM_RE = re.compile(
    r"""
    \b(?:
        clause\s*61|
        lpp\s*\d+[a-z]?|
        tpp\s*\d+|
        spp\s*3\.?\s*7|
        lps\s*5?|
        r-?codes?|
        bal-?\d+|
        bal\b|
        outbuilding|
        shipping\s+container|
        ancillary(?:\s+dwelling)?|
        granny\s+flat|
        setback|
        bushfire|
        exempt(?:ion|ions)?|
        deemed\s+to\s+comply|
        development\s+approval|
        water\s+tank|
        stormwater|
        dividing\s+fence|
        heritage|
        structure\s+plan|
        child\s+care|
        family\s+day\s+care|
        holiday\s+house|
        nature\s+based\s+park|
        caravan\s+park
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


@lru_cache(maxsize=1)
def _client():
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _normalize(text: str) -> str:
    text = text.lower().replace("-", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def extract_search_terms(query_text: str | None, *, limit: int = 6) -> list[str]:
    """Pull exact policy phrases + useful keywords from the user question."""
    if not query_text or not query_text.strip():
        return []

    terms: list[str] = []
    seen: set[str] = set()

    def _add(term: str) -> None:
        cleaned = " ".join(term.strip().split())
        if len(cleaned) < 2:
            return
        key = cleaned.lower()
        if key in seen:
            return
        seen.add(key)
        terms.append(cleaned)

    for match in _POLICY_TERM_RE.finditer(query_text):
        _add(match.group(0))

    # Compact codes people type: LPP3, Clause61, BAL29
    for match in re.finditer(
        r"\b(?:LPP|TPP|SPP|LPS|BAL|R)\s*[-.]?\s*\d+[A-Za-z]?\b",
        query_text,
        flags=re.IGNORECASE,
    ):
        _add(re.sub(r"\s+", "", match.group(0)))

    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", query_text):
        low = token.lower()
        if low in _STOPWORDS:
            continue
        _add(token)

    return terms[:limit]


def _escape_ilike(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _canonical_zones_in(text: str) -> set[str]:
    """Return canonical zone names mentioned in free-text applicable_zones."""
    n = _normalize(text)
    if not n:
        return set()
    padded = f" {n} "
    found: set[str] = set()
    for zone in _CANONICAL_ZONES:
        if f" {zone} " in padded:
            found.add(zone)
    return {
        z
        for z in found
        if not any(z != other and z in other for other in found)
    }


def _is_all_zones(applicable: str) -> bool:
    n = _normalize(applicable)
    if not n:
        return False
    if n in {"all zones", "all zone", "statewide", "n a", "na"}:
        return True
    if n.startswith("all zones"):
        return True
    if "all zones" in n and "site specific" in n:
        return True
    return False


def zone_match_score(live_zone: str | None, applicable_zones: str | None) -> float:
    """Soft score adjustment for zone fit."""
    if not live_zone or not live_zone.strip():
        return 0.0

    applicable = (applicable_zones or "").strip()
    if not applicable:
        return 0.0

    if _is_all_zones(applicable):
        return _ALL_ZONES_BOOST

    live_keys = _canonical_zones_in(live_zone)
    applicable_keys = _canonical_zones_in(applicable)

    if live_keys and applicable_keys and live_keys & applicable_keys:
        return _ZONE_BOOST

    live_norm = _normalize(live_zone)
    applicable_norm = _normalize(applicable)
    if (
        not live_keys
        and not applicable_keys
        and live_norm
        and len(live_norm) >= 4
        and f" {live_norm} " in f" {applicable_norm} "
    ):
        return _ZONE_BOOST

    if applicable_keys and live_keys and not (live_keys & applicable_keys):
        return _MISMATCH_PENALTY

    if applicable_keys and not live_keys:
        return _MISMATCH_PENALTY

    return 0.0


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    *,
    k: int = _RRF_K,
    limit: int | None = None,
) -> list[dict]:
    """Merge ranked result lists with Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    best_row: dict[str, dict] = {}

    for rows in ranked_lists:
        for rank, row in enumerate(rows, start=1):
            rid = str(row.get("id") or "")
            if not rid:
                continue
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank)
            prev = best_row.get(rid)
            if prev is None:
                best_row[rid] = dict(row)
                continue
            # Keep higher vector similarity when both lists have the same id
            try:
                prev_sim = float(prev.get("similarity") or 0.0)
            except (TypeError, ValueError):
                prev_sim = 0.0
            try:
                cur_sim = float(row.get("similarity") or 0.0)
            except (TypeError, ValueError):
                cur_sim = 0.0
            if cur_sim >= prev_sim:
                merged = {**prev, **row}
            else:
                merged = {**row, **prev}
            best_row[rid] = merged

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    out: list[dict] = []
    for rid, rrf in ordered:
        row = best_row[rid]
        row["rrf_score"] = rrf
        # Ensure similarity exists for downstream zone re-rank
        if row.get("similarity") is None:
            row["similarity"] = rrf
        out.append(row)
        if limit is not None and len(out) >= limit:
            break
    return out


def _keyword_search(
    terms: list[str],
    *,
    limit: int,
) -> list[dict]:
    """Exact/phrase-ish search over policy text fields via PostgREST ilike."""
    if not terms or limit <= 0:
        return []

    client = _client()
    hits_by_id: dict[str, dict] = {}

    for term in terms:
        pattern = f"%{_escape_ilike(term)}%"
        try:
            result = (
                client.table("policy_chunks")
                .select(
                    "id,document,source_document,topic,applicable_zones,page,"
                    "clause_type,section,subsection,item_ref,doc_priority"
                )
                .eq("is_dummy", False)
                .or_(
                    "document.ilike.{0},topic.ilike.{0},source_document.ilike.{0},"
                    "section.ilike.{0},embed_text.ilike.{0}".format(pattern)
                )
                .limit(limit)
                .execute()
            )
        except Exception:
            logger.exception("Keyword search failed for term=%r", term)
            continue

        for row in result.data or []:
            rid = str(row.get("id") or "")
            if not rid:
                continue
            existing = hits_by_id.get(rid)
            if existing is None:
                hits_by_id[rid] = {
                    **row,
                    "similarity": 0.55,  # synthetic score so zone re-rank works
                    "keyword_hit": True,
                    "keyword_terms": [term],
                }
            else:
                terms_hit = list(existing.get("keyword_terms") or [])
                if term not in terms_hit:
                    terms_hit.append(term)
                existing["keyword_terms"] = terms_hit
                # More matching terms → slightly higher synthetic score
                existing["similarity"] = min(0.85, 0.50 + 0.08 * len(terms_hit))

    # Prefer rows that matched more keyword terms
    ranked = sorted(
        hits_by_id.values(),
        key=lambda r: (len(r.get("keyword_terms") or []), float(r.get("similarity") or 0)),
        reverse=True,
    )
    return ranked[:limit]


def _vector_search(
    query_embedding: list[float],
    *,
    match_count: int,
) -> list[dict]:
    client = _client()
    result = (
        client.rpc(
            "match_policy_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "filter_source": None,
                "include_dummy": False,
            },
        )
        .execute()
    )
    return list(result.data or [])


def _enrich_rows(rows: list[dict]) -> list[dict]:
    ids = [str(r.get("id")) for r in rows if r.get("id")]
    if not ids:
        return rows

    client = _client()
    detail = (
        client.table("policy_chunks")
        .select(
            "id,section,subsection,page,topic,item_ref,source_document,"
            "document,clause_type,applicable_zones"
        )
        .in_("id", ids)
        .execute()
    )
    by_id = {str(r["id"]): r for r in (detail.data or [])}
    enriched: list[dict] = []
    for row in rows:
        rid = str(row.get("id"))
        extra = by_id.get(rid, {})
        enriched.append({**row, **extra})
    return enriched


def _rerank_by_zone(
    rows: list[dict],
    *,
    zone_name: str | None,
    match_count: int,
) -> list[dict]:
    if not rows:
        return rows

    scored: list[tuple[float, float, dict]] = []
    for row in rows:
        try:
            sim = float(row.get("similarity") or 0.0)
        except (TypeError, ValueError):
            sim = 0.0
        try:
            rrf = float(row.get("rrf_score") or 0.0)
        except (TypeError, ValueError):
            rrf = 0.0
        # RRF values are small (~0.01–0.05); scale so keyword hits remain visible
        # beside vector similarity, then apply the softer zone adjustment.
        base = sim + (rrf * 15.0 if rrf else 0.0)
        boost = zone_match_score(zone_name, row.get("applicable_zones"))
        final = base + boost
        row = {**row, "zone_boost": boost, "zone_rank_score": final}
        scored.append((final, sim, row))

    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [row for _, _, row in scored[:match_count]]


def search_policies(
    query_embedding: list[float],
    *,
    match_count: int = 5,
    zone_name: str | None = None,
    query_text: str | None = None,
) -> list[dict]:
    """Hybrid retrieve: vector + keyword, then optional zone soft re-rank."""
    settings = get_settings()
    fetch_count = match_count
    if zone_name or settings.hybrid_search:
        fetch_count = min(
            max(match_count * _CANDIDATE_MULTIPLIER, match_count),
            _CANDIDATE_CAP,
        )

    vector_rows = _vector_search(query_embedding, match_count=fetch_count)

    keyword_rows: list[dict] = []
    terms: list[str] = []
    if settings.hybrid_search:
        terms = extract_search_terms(query_text)
        if terms:
            keyword_rows = _keyword_search(terms, limit=fetch_count)

    if keyword_rows:
        rows = reciprocal_rank_fusion(
            [vector_rows, keyword_rows],
            limit=fetch_count,
        )
        logger.info(
            "RAG hybrid merge vector=%s keyword=%s terms=%s fused=%s",
            len(vector_rows),
            len(keyword_rows),
            terms,
            len(rows),
        )
    else:
        rows = vector_rows
        if settings.hybrid_search:
            logger.info("RAG hybrid skipped keyword (no useful terms) q=%r", (query_text or "")[:80])

    rows = _enrich_rows(rows)

    if zone_name:
        before = [str(r.get("id")) for r in rows[:match_count]]
        rows = _rerank_by_zone(rows, zone_name=zone_name, match_count=match_count)
        after = [str(r.get("id")) for r in rows]
        logger.info(
            "RAG zone re-rank zone=%r candidates=%s kept=%s order_changed=%s",
            zone_name,
            fetch_count,
            len(rows),
            before != after,
        )
    elif len(rows) > match_count:
        rows = rows[:match_count]

    logger.info("RAG retrieve: %s hits", len(rows))
    for i, row in enumerate(rows, start=1):
        sim = row.get("similarity")
        sim_s = f"{float(sim):.3f}" if sim is not None else "?"
        boost = row.get("zone_boost")
        boost_s = f"{float(boost):+.2f}" if boost is not None else "n/a"
        rrf = row.get("rrf_score")
        rrf_s = f"{float(rrf):.4f}" if rrf is not None else "n/a"
        logger.info(
            "  [%s] id=%s source=%s page=%s sim=%s rrf=%s zone_boost=%s kw=%s",
            i,
            row.get("id"),
            row.get("source_document"),
            row.get("page"),
            sim_s,
            rrf_s,
            boost_s,
            row.get("keyword_terms") or [],
        )
    return rows
