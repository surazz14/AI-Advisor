"""Answer generation from retrieved policy clauses.

Providers (set LLM_PROVIDER, or leave as auto):
  - huggingface  — free HF Inference Providers (HF_TOKEN)
  - groq         — free Groq API (GROQ_API_KEY) — usually fastest/most reliable free tier
  - gemini       — Google Gemini (GEMINI_API_KEY)
  - auto         — first configured of: groq → huggingface → gemini → simple summary
"""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request

import certifi

from app.config import get_settings
from app.services.heritage_lookup import HeritageInfo
from app.services.rcode_lookup import RCodeInfo


# Room for the model's hidden reasoning (gpt-oss counts it against this limit)
# plus a ~200-word answer: real answers use ~500–760. At 700, longer ones were
# cut off. Kept modest because Groq's free tier counts it against 8k tokens/min.
MAX_ANSWER_TOKENS = 1400
# On a 429, retry (up to 3 attempts) while the total wait for Groq's per-minute
# window stays under this — well inside the frontend's 120 s reply timeout.
MAX_RATE_LIMIT_WAIT_S = 30.0
RATE_LIMIT_ATTEMPTS = 3

SYSTEM_PROMPT = """You are the Plantagenet Planning Advisor: a practical, knowledgeable planning \
assistant for property owners in the Shire of Plantagenet, Western Australia.

Grounding
- Base every rule, number, limit and approval requirement on the numbered policy clauses \
provided, and cite them like [1], [2]. Never invent rules or numbers, or use rules from \
other councils. If a rule the user needs is not in the clauses, say briefly what is not covered.
- Use only clauses that fit this property and this question. Ignore clauses written for other \
zones (e.g. Residential-only R-Codes limits on a Rural lot) and situations the user has ruled out \
(e.g. boundary-fence rules when they say the fence is internal).
- When a Shire policy written for this zone and a general standard (such as the R-Codes) set \
different limits, apply the Shire policy for this zone.

Property facts
- The property facts (zone, lot area, R-Code, bushfire map, heritage) come from official \
government map layers. Treat them as reliable and use them directly. Never ask the user to \
check or confirm them.

Stay on the question
- Answer what was asked. Do not add side topics.
- Mention bushfire only when the question is about bushfire, or a provided clause makes \
bushfire requirements apply to this kind of work (e.g. a new dwelling in a bushfire prone area).
- Mention heritage only when it changes the answer.

Be useful and decisive
- Start with a direct answer (yes / no / yes, if ...), then the conditions that matter.
- When the clauses settle the question, say so plainly. Suggest contacting the Shire only \
when the outcome genuinely depends on Shire discretion or information you don't have: at most \
once, at the end, saying exactly what to ask.
- Do not add "guidance only" disclaimers; the app shows one under every answer.

Question styles
- "Can I ... / Do I need approval ..." questions: direct answer, then only the limits and \
conditions that decide it. No step-by-step plan unless the user asks how to go about it.
- "How should I ... / What's the best way to approach ..." questions: give a short practical \
plan as numbered steps (what to check first, which approvals or reports are needed and in what \
order, and design choices that make approval simpler), citing a clause for each rule. Practical \
sequencing advice is welcome as long as it does not contradict the clauses.

Format
- Be succinct; users value short answers. "Can I" answers: under 150 words. \
"How should I / best way" answers: under 250 words. Plain language, short bullets."""


def suggest_followup_query(
    *,
    question: str,
    first_hits: list[dict],
    zone_name: str | None = None,
) -> str | None:
    """Build a second-hop search query from the question + first retrieval gaps.

    Heuristic only (fast/cheap). Returns None when a second hop is unlikely to help.
    """
    q = (question or "").strip().lower()
    if not q:
        return None

    sources = {
        str(row.get("source_document") or "").strip()
        for row in first_hits
        if row.get("source_document")
    }
    topics = " ".join(
        str(row.get("topic") or "") for row in first_hits
    ).lower()

    zone_bit = f" {zone_name}" if zone_name else ""
    followups: list[str] = []

    wants_shed = any(
        w in q
        for w in (
            "shed",
            "outbuilding",
            "garage",
            "shipping container",
            "container",
            "plant room",
            "pump house",
            "pump room",
            "workshop",
            "storage building",
            "small building",
        )
    )
    wants_fence = any(w in q for w in ("fence", "fencing", "dividing fence", "pool barrier"))
    wants_bushfire = any(
        w in q for w in ("bushfire", "bush fire", "bal", "fire prone", "flame")
    )
    wants_dwelling = any(
        w in q for w in ("house", "dwelling", "ancillary", "relocated", "transportable")
    )
    wants_ancillary = any(
        w in q
        for w in (
            "ancillary",
            "granny flat",
            "grannyflat",
            "secondary dwelling",
            "studio apartment",
            "dependant persons",
        )
    )
    wants_childcare = any(
        w in q
        for w in (
            "child care",
            "childcare",
            "family day care",
            "daycare",
            "day care",
            "creche",
            "crèche",
        )
    )
    wants_tourism = any(
        w in q
        for w in (
            "tourism",
            "tourist",
            "bed and breakfast",
            "b&b",
            "bnb",
            "chalet",
            "holiday house",
            "holiday accommodation",
            "short-term",
            "short term",
            "airbnb",
            "hipcamp",
            "caravan park",
            "nature based park",
            "nature-based",
            "glamping",
            "eco-tourism",
            "ecotourism",
        )
    )
    wants_reserve = any(
        w in q
        for w in (
            "reserve",
            "class a reserve",
            "crown land",
            "management order",
            "management body",
            "conservation reserve",
            "national park",
            "land administration act",
        )
    )
    wants_heritage = any(
        w in q
        for w in (
            "heritage",
            "heritage listed",
            "heritage-listed",
            "state register",
            "municipal inventory",
            "inherit",
            "aboriginal heritage",
            "aboriginal site",
            "cultural heritage",
            "achis",
        )
    )
    wants_structure_plan = any(
        w in q
        for w in (
            "structure plan",
            "subdivision guide",
            "porongurup",
            "hambley",
            "stoney creek",
            "rural village",
            "mira flores",
            "building envelope",
        )
    )
    wants_zone = any(w in q for w in ("zone", "zoning", "permitted", "land use"))
    wants_water_tank = any(w in q for w in ("water tank", "watertank", "rainwater tank"))
    wants_stormwater = any(
        w in q for w in ("stormwater", "soakwell", "retention", "drainage", "runoff")
    )
    wants_dam = any(w in q for w in ("dam", "water feature", "pond", "weir"))
    wants_exemption = any(
        w in q
        for w in (
            "need approval",
            "planning approval",
            "development approval",
            "exempt",
            "exemption",
            "deemed to comply",
            "do i need",
            "clause 61",
        )
    )

    has_lpp3 = "LPP3" in sources
    has_spp37 = "SPP3.7_Guidelines" in sources
    has_fence = any(
        s.startswith("Dividing Fences")
        or "Building Regulations" in s
        or "Plantagenet" in s
        or s == "LPP-Fencing"
        for s in sources
    )
    has_lps5 = "LPS5" in sources
    has_rcodes = "R-Codes-Vol1-2026" in sources
    has_lpp6 = "LPP6" in sources
    has_lpp7 = "LPP7" in sources or "LPP7 Info Brochure" in sources
    has_lpp8 = "LPP8" in sources or "LPP8 Info Brochure" in sources
    has_c61 = any(
        "Clause 61" in s or "Schedule 2" in s or s == "Clause61-DeemedProvisions"
        for s in sources
    )
    has_lpp5 = "LPP5" in sources
    has_lpp1 = "LPP1" in sources
    has_lpp2 = "LPP2" in sources
    has_lpp4 = "LPP4" in sources
    has_lpp5b = "LPP5-SingleHouseExemptions" in sources
    has_laa = "Land Administration Act 1997" in sources
    has_heritage = "Heritage List (inHerit)" in sources
    has_abh = "Aboriginal Heritage Act 1972" in sources
    has_structure = (
        "Structure Plans (WAPC-approved)" in sources
        or "TPP18.1 Appendix 4 - Porongurup Rural Village" in sources
    )

    # Fill gaps the first hop likely missed
    if wants_shed and not has_lpp3:
        followups.append(
            f"outbuilding shed size limits deemed to comply shipping container{zone_bit}"
        )
    if wants_bushfire and not has_spp37:
        followups.append(
            "bushfire prone BAL rating SPP 3.7 exemption incidental non-habitable structure"
        )
    if wants_fence and not has_fence:
        followups.append(
            "dividing fence front fence height visually permeable building permit pool barrier"
        )
    if wants_water_tank and not has_lpp6:
        followups.append(
            f"water tank size height limits deemed to comply building permit{zone_bit}"
        )
    if wants_stormwater and not has_lpp7:
        followups.append(
            "stormwater on-site retention volume roof area soakwell overflow discharge"
        )
    if wants_dam and not has_lpp8:
        followups.append(
            f"dam water feature exemption setbacks waterway wetland approval{zone_bit}"
        )
    if wants_ancillary and not has_lpp1:
        followups.append(
            f"ancillary dwelling plot ratio 100m2 potable water setback bushfire{zone_bit}"
        )
    if wants_childcare and not has_lpp4:
        followups.append(
            "child care premises family day care lot size parking hours outdoor play space"
        )
    if wants_tourism and not has_lpp2:
        followups.append(
            "tourism development bed breakfast chalet holiday house management plan water tank bushfire"
        )
    if wants_reserve and not has_laa:
        followups.append(
            "crown reserve class A management body lease purpose change Land Administration Act"
        )
    if wants_heritage and not has_heritage:
        followups.append(
            "heritage listed place Plantagenet State Register Municipal Inventory exemption"
        )
    if wants_heritage and ("aboriginal" in q or "achis" in q or "cultural" in q) and not has_abh:
        followups.append(
            "Aboriginal Heritage Act site protection ACHIS ministerial approval"
        )
    if wants_structure_plan and not has_structure:
        followups.append(
            "structure plan Porongurup Rural Village precinct setback subdivision guide expiry"
        )
    if wants_exemption and not has_c61:
        followups.append(
            "clause 61 development approval not required works use single house outbuilding exemption"
        )
    if wants_exemption and has_c61 and not has_lpp5 and not has_lpp5b:
        followups.append(
            "local planning policy 5 exemptions from development approval plantagenet"
        )
    if (
        wants_dwelling
        and wants_exemption
        and not has_lpp5b
        and any(w in q for w in ("rural", "non-residential", "single house", "exempt"))
    ):
        followups.append(
            "single house exemption non-residential zone BAL-29 height clearing LPP5"
        )
    if wants_dwelling and "POL5-RELOC" not in sources and "reloc" in q:
        followups.append("relocated transportable dwelling local policy requirements")
    if wants_zone and not has_lps5:
        followups.append(f"local planning scheme zone objectives land use{zone_bit}")

    # Compound questions: if we got sheds but not bushfire (or reverse), chase the other
    if wants_shed and wants_bushfire:
        if has_lpp3 and not has_spp37:
            followups.append(
                "outbuilding shed in bushfire prone area SPP 3.7 6 metre exemption"
            )
        elif has_spp37 and not has_lpp3:
            followups.append(
                f"outbuilding floor area wall height ridge height Rural Residential{zone_bit}"
            )

    if wants_fence and has_rcodes and "front" in q and "permeab" not in topics:
        followups.append("primary street setback fence visually permeable 1.2m R-Codes")
    if any(w in q for w in ("setback", "boundary setback", "wall setback", "privacy")) and not any(
        "setback" in (row.get("topic") or "").lower() for row in first_hits
    ):
        followups.append(
            "R-Codes lot boundary wall setback table privacy cone of vision retaining wall"
        )

    # De-dupe while preserving order
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in followups:
        key = item.strip().lower()
        if key and key not in seen and key != q:
            seen.add(key)
            cleaned.append(item.strip())

    if not cleaned:
        # Soft second hop: rephrase toward related standards when first hits exist
        if not first_hits:
            return None
        if wants_shed:
            return f"outbuilding size limits floor area wall height ridge height{zone_bit}".strip()
        if wants_fence:
            return "dividing fences act neighbour contribution sufficient fence"
        if wants_bushfire:
            return "bushfire management BAL-29 asset protection zone dwelling"
        if wants_water_tank:
            return f"water tank deemed to comply size height Rural Residential{zone_bit}".strip()
        if wants_stormwater:
            return "stormwater retention 1 cubic metre per 100 square metres roof"
        if wants_dam:
            return "dam exemption setback waterway wetland spillway approval"
        if wants_exemption:
            return "clause 61 schedule 2 development approval not required exemptions"
        if wants_ancillary:
            return f"ancillary dwelling maximum plot ratio potable water setback{zone_bit}".strip()
        if wants_childcare:
            return "child care premises parking landscaping operating hours family day care"
        if wants_tourism:
            return "tourist development chalet holiday house management plan unit limit bushfire"
        if wants_reserve:
            return "crown reserve class A management order lease excision purpose change"
        if wants_heritage:
            if "aboriginal" in q:
                return "Aboriginal Heritage Act protected site ACHIS ministerial approval"
            return "heritage listed place Plantagenet State Register Municipal Inventory"
        if wants_structure_plan:
            return "Porongurup Rural Village structure plan precinct setback drainage"
        return None

    # One focused follow-up query (keep it short for embedding quality)
    return cleaned[0]


def _chat_completion(*, user_prompt: str, system_prompt: str | None = None) -> str:
    """Run a one-shot chat with the configured provider. Empty string on failure."""
    settings = get_settings()
    provider = _resolve_provider(settings)
    system = system_prompt or SYSTEM_PROMPT
    full_user = user_prompt
    # Providers that support a separate system role get it; Gemini uses system_instruction.
    try:
        if provider == "groq":
            return _openai_compatible_chat(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                user_prompt=full_user,
                system_prompt=system,
            )
        if provider == "huggingface":
            return _huggingface_chat(
                api_key=settings.hf_token,
                model=settings.hf_model,
                user_prompt=full_user,
                system_prompt=system,
            )
        if provider == "gemini":
            return _gemini_answer(
                user_prompt=full_user,
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                system_prompt=system,
            )
    except Exception as exc:
        print(f"[llm] completion failed ({provider}): {exc}", flush=True)
    return ""


def generate_answer(
    *,
    question: str,
    address: str | None,
    clauses: list[dict],
    zone_name: str | None = None,
    bushfire_note: str | None = None,
    lot_area_m2: float | None = None,
    lot_count: int | None = None,
    rcode: RCodeInfo | None = None,
    heritage: HeritageInfo | None = None,
    heritage_checked: bool = False,
) -> str:
    """Generate a short answer from retrieved clauses via the configured LLM."""
    context = _format_clauses(clauses)
    location = address or "the selected property"
    if zone_name:
        location = f"{location} (zone: {zone_name})"
    if lot_area_m2:
        location = (
            f"{location}\nLot area: approx. {lot_area_m2:,.0f} m² "
            f"({lot_area_m2 / 10_000:.2f} ha) from the Landgate cadastre (official) — "
            "use it to pick the matching lot-size limits"
        )
        if lot_count and lot_count > 1:
            location = (
                f"{location}\nThis address covers {lot_count} separate lots; the "
                "area above is their total. Mention that limits may apply per lot"
            )
    if rcode and rcode.alternative:
        location = (
            f"{location}\nR-Code: {rcode.code} (dual code) — apply "
            f"{rcode.base} by default; {rcode.alternative} only applies if the "
            "scheme's conditions for the higher code are met, so say so"
        )
    elif rcode:
        location = f"{location}\nR-Code: {rcode.code} — use the R-Codes standards for this density"
    elif zone_name and not zone_name.strip().lower().startswith("residential"):
        # get_rcode returns None for "no R-Code" and for lookup failures alike.
        location = (
            f"{location}\nR-Code: none found for this lot — in a {zone_name} zone, prefer "
            "Shire policies written for this zone over R-Codes limits"
        )
    heritage_note = _heritage_prompt(heritage, checked=heritage_checked)
    if heritage_note:
        location = f"{location}\n{heritage_note}"

    map_note = f"\n\nMap check: {bushfire_note}" if bushfire_note else ""
    user_prompt = (
        f"Property: {location}\n\n"
        f"Question: {question}{map_note}\n\n"
        f"Policy clauses:\n{context}\n\n"
        "Answer the question using the clauses that apply, with citations like [1], [2]."
    )

    text = _chat_completion(user_prompt=user_prompt)
    if text:
        return text
    return _simple_answer(question=question, location=location, clauses=clauses)


def _heritage_prompt(heritage: HeritageInfo | None, *, checked: bool) -> str | None:
    """Heritage instructions for the LLM (None = nothing to add)."""
    if not checked:
        return None
    if heritage is None:
        return (
            "Heritage: status UNKNOWN (lookup failed) — do not say works are exempt "
            "without telling the user to first confirm heritage status with the Shire"
        )
    notes: list[str] = []
    if heritage.statutory:
        names = "; ".join(m.describe() for m in heritage.statutory)
        notes.append(
            f"Heritage: the lot is HERITAGE-PROTECTED ({names}). Many clause 61 "
            "development-approval exemptions do not apply to heritage-protected "
            "places — do not say works are exempt; say development approval is "
            "likely required and to contact the Shire before starting"
        )
    elif heritage.survey_only:
        notes.append(
            "Heritage: the place is on the Local Heritage Survey only (information "
            "only, not a statutory listing) — mention it, but it does not by itself "
            "remove exemptions"
        )
    if heritage.aboriginal:
        notes.append(
            "Aboriginal heritage: a recorded Aboriginal heritage place overlaps the "
            "lot — say that ground-disturbing works may need consideration under the "
            "Aboriginal Heritage Act 1972 and to check with DPLH"
        )
    if not notes:
        notes.append(
            "Heritage: no State Register, Heritage List, Heritage Area or Aboriginal "
            "heritage listing found on the lot"
        )
    if heritage.incomplete:
        notes.append("(some heritage layers could not be checked)")
    return "\n".join(notes)


def _resolve_provider(settings) -> str:
    preferred = (settings.llm_provider or "auto").strip().lower()
    if preferred in {"groq", "huggingface", "gemini"}:
        if preferred == "groq" and settings.groq_api_key:
            return "groq"
        if preferred == "huggingface" and settings.hf_token:
            return "huggingface"
        if preferred == "gemini" and settings.gemini_api_key:
            return "gemini"
        return "none"

    # auto: prefer free providers first
    if settings.groq_api_key:
        return "groq"
    if settings.hf_token:
        return "huggingface"
    if settings.gemini_api_key:
        return "gemini"
    return "none"


def _format_clauses(clauses: list[dict]) -> str:
    blocks = []
    for i, row in enumerate(clauses, start=1):
        zones = f" | applies to: {row['applicable_zones']}" if row.get("applicable_zones") else ""
        blocks.append(
            f"[{i}] id={row.get('id')} | source={row.get('source_document')} | "
            f"topic={row.get('topic')}{zones}\n{row.get('document')}"
        )
    return "\n\n".join(blocks) if blocks else "(no clauses retrieved)"


def _huggingface_chat(
    *,
    api_key: str,
    model: str,
    user_prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    """Hugging Face Inference Providers (chat completions)."""
    from huggingface_hub import InferenceClient

    client = InferenceClient(api_key=api_key, provider="auto")
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_ANSWER_TOKENS,
    )
    return (completion.choices[0].message.content or "").strip()


def _openai_compatible_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    user_prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    """OpenAI-compatible chat (Groq, etc.) via stdlib — no extra SDK required."""
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": MAX_ANSWER_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Groq's Cloudflare front rejects urllib's default UA (error 1010).
            "User-Agent": "PlantagenetPlanningAdvisor/0.1",
        },
        method="POST",
    )
    # certifi's CA bundle: python.org macOS builds ship without system certs.
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    waited = 0.0
    for attempt in range(RATE_LIMIT_ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=90, context=ssl_context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            wait = _rate_limit_wait(exc) if exc.code == 429 else None
            if (
                wait is not None
                and attempt < RATE_LIMIT_ATTEMPTS - 1
                and waited + wait <= MAX_RATE_LIMIT_WAIT_S
            ):
                print(f"[llm] rate limited ({model}); retrying in {wait:.1f}s", flush=True)
                time.sleep(wait)
                waited += wait
                continue
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc

    choices = data.get("choices") or []
    if not choices:
        return ""
    if choices[0].get("finish_reason") == "length":
        print(f"[llm] answer hit max_tokens={MAX_ANSWER_TOKENS} and was cut off ({model})", flush=True)
    message = choices[0].get("message") or {}
    return (message.get("content") or "").strip()


def _rate_limit_wait(exc: urllib.error.HTTPError) -> float | None:
    """Seconds to wait from a 429's headers (Retry-After, or Groq's token reset)."""
    retry_after = exc.headers.get("retry-after")
    if retry_after:
        try:
            return float(retry_after) + 1.0
        except ValueError:
            pass
    # Groq format, e.g. "7.66s" or "1m2.5s"
    reset = exc.headers.get("x-ratelimit-reset-tokens") or ""
    match = re.fullmatch(r"(?:(\d+)m)?([\d.]+)s", reset.strip())
    if match:
        return int(match.group(1) or 0) * 60 + float(match.group(2)) + 1.0
    return None


def _gemini_answer(
    *,
    user_prompt: str,
    api_key: str,
    model: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    llm = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt,
    )
    response = llm.generate_content(
        user_prompt,
        generation_config={"temperature": 0.2},
    )
    return (getattr(response, "text", None) or "").strip()


def _simple_answer(*, question: str, location: str, clauses: list[dict]) -> str:
    if not clauses:
        return (
            f"Using property: **{location}**\n\n"
            "I could not find matching policy clauses for that question. "
            "Try asking about sheds, fences, dwellings, setbacks, or zoning.\n\n"
            "*Guidance only — not a formal planning decision.*"
        )

    lines = [
        f"Using property: **{location}**",
        "",
        f"For your question (“{question.strip()}”), these policy clauses look most relevant:",
        "",
    ]
    for i, row in enumerate(clauses[:5], start=1):
        doc = row.get("source_document") or "policy"
        topic = row.get("topic") or row.get("id") or "clause"
        text = (row.get("document") or "").strip()
        if len(text) > 280:
            text = text[:277] + "..."
        lines.append(f"**[{i}] {doc} — {topic}**")
        lines.append(text)
        lines.append("")

    lines.append(
        "*Simple retrieval reply (set GROQ_API_KEY or HF_TOKEN for a written summary). "
        "Guidance only — not a formal planning decision.*"
    )
    return "\n".join(lines)
