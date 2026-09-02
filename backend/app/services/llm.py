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
    wants_zone = any(w in q for w in ("zone", "zoning", "permitted", "land use"))

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
