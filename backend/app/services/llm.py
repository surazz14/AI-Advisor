"""Simple answer generation from retrieved policy clauses (Gemini)."""

from __future__ import annotations

from app.config import get_settings


SYSTEM_PROMPT = """You are the Plantagenet Planning Advisor chatbot.
Answer ONLY using the policy clauses provided.
Be short and clear (about 4–8 sentences).
If the clauses are not enough, say what is missing.
Always say this is guidance only, not a formal planning decision.
Do not invent rules from other shires."""


def generate_answer(
    *,
    question: str,
    address: str | None,
    clauses: list[dict],
    zone_name: str | None = None,
) -> str:
    """Prefer Gemini if configured; otherwise build a simple clause summary."""
    settings = get_settings()
    context = _format_clauses(clauses)
    location = address or "the selected property"
    if zone_name:
        location = f"{location} (zone: {zone_name})"

    if settings.gemini_api_key:
        return _gemini_answer(
            question=question,
            location=location,
            context=context,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    return _simple_answer(question=question, location=location, clauses=clauses)


def _format_clauses(clauses: list[dict]) -> str:
    blocks = []
    for i, row in enumerate(clauses, start=1):
        blocks.append(
            f"[{i}] id={row.get('id')} | source={row.get('source_document')} | "
            f"topic={row.get('topic')}\n{row.get('document')}"
        )
    return "\n\n".join(blocks) if blocks else "(no clauses retrieved)"


def _gemini_answer(
    *,
    question: str,
    location: str,
    context: str,
    api_key: str,
    model: str,
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    llm = genai.GenerativeModel(
        model_name=model,
        system_instruction=SYSTEM_PROMPT,
    )
    prompt = (
        f"Property: {location}\n\n"
        f"Question: {question}\n\n"
        f"Policy clauses:\n{context}\n\n"
        "Write a short helpful answer with citations like [1], [2]."
    )
    response = llm.generate_content(
        prompt,
        generation_config={"temperature": 0.2},
    )
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        return _simple_answer(question=question, location=location, clauses=[])
    return text


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
        "*Simple retrieval reply (set GEMINI_API_KEY for a written summary). "
        "Guidance only — not a formal planning decision.*"
    )
    return "\n".join(lines)
