"""Answer generation from retrieved policy clauses.

Providers (set LLM_PROVIDER, or leave as auto):
  - huggingface  — free HF Inference Providers (HF_TOKEN)
  - groq         — free Groq API (GROQ_API_KEY) — usually fastest/most reliable free tier
  - gemini       — Google Gemini (GEMINI_API_KEY)
  - auto         — first configured of: groq → huggingface → gemini → simple summary
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.config import get_settings


SYSTEM_PROMPT = """You are the Plantagenet Planning Advisor chatbot.
Answer ONLY using the policy clauses provided.
Be short and clear (about 4–8 sentences).
If the clauses are not enough, say what is missing.
Always say this is guidance only, not a formal planning decision.
Do not invent rules from other shires."""


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
        w in q for w in ("shed", "outbuilding", "garage", "shipping container", "container")
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
            return f"outbuilding acceptable development standards setbacks{zone_bit}".strip()
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
        print(f"[llm] completion failed ({provider}): {exc}")
    return ""


def generate_answer(
    *,
    question: str,
    address: str | None,
    clauses: list[dict],
    zone_name: str | None = None,
) -> str:
    """Generate a short answer from retrieved clauses via the configured LLM."""
    context = _format_clauses(clauses)
    location = address or "the selected property"
    if zone_name:
        location = f"{location} (zone: {zone_name})"

    user_prompt = (
        f"Property: {location}\n\n"
        f"Question: {question}\n\n"
        f"Policy clauses:\n{context}\n\n"
        "Write a short helpful answer with citations like [1], [2]."
    )

    text = _chat_completion(user_prompt=user_prompt)
    if text:
        return text
    return _simple_answer(question=question, location=location, clauses=clauses)


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
        blocks.append(
            f"[{i}] id={row.get('id')} | source={row.get('source_document')} | "
            f"topic={row.get('topic')}\n{row.get('document')}"
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
        max_tokens=700,
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
        "max_tokens": 700,
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
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc

    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return (message.get("content") or "").strip()


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
