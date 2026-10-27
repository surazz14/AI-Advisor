"""Trust score: how much of an answer is backed by retrieved facts vs the LLM.

Deterministic — the model never rates itself. Two checks:
  1. Statement support: each statement is backed if it cites a clause, or if
     every figure in it comes from the sources (e.g. "your 120 m² shed is
     within the limit"). Uncited statements without figures — conclusions and
     reasoning — can't be checked either way and count half.
  2. Figure support: share of the numbers in the answer (200 m², 4.5 m,
     400 000 L …) that appear in the cited clauses, the property facts or the
     user's question. A figure found in none of them came from the model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HIGH_THRESHOLD = 75
MEDIUM_THRESHOLD = 50

_CITATION = re.compile(r"\[\d+(?:\s*[,–—‑-]\s*\d+)*\]")
# Group separators inside numbers: "400,000", "400 000" (incl. thin/narrow spaces).
_THOUSANDS = re.compile(r"(?<=\d)[,    ](?=\d{3}(?!\d))")
# A figure not preceded by a letter or digit, so "m2", "R12.5", "LPP3" and
# "C61_0002" don't count; a trailing unit is fine ("200m2", "4.5m", "10ha").
_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\.?\d)")
_LIST_MARKER = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*(])")


@dataclass
class TrustResult:
    score: int
    level: str  # "high" | "medium" | "low"
    cited_statements: int = 0
    total_statements: int = 0
    supported_figures: int = 0
    total_figures: int = 0
    unsupported_figures: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _level(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def _figures(text: str) -> list[str]:
    text = _CITATION.sub(" ", text)
    text = _THOUSANDS.sub("", text)
    return _NUMBER.findall(text)


def _as_number(token: str) -> float:
    return float(token)


def _statements(answer: str) -> list[str]:
    """Split the answer into statements worth checking (skip headings, filler)."""
    statements: list[str] = []
    for raw_line in answer.splitlines():
        line = _LIST_MARKER.sub("", raw_line).strip()
        if not line:
            continue
        plain = line.replace("*", "").replace("_", "").strip()
        # Headings like "**Key requirements**" or "What to do:".
        if plain.endswith(":") or (line.startswith("**") and line.endswith("**")):
            continue
        for sentence in _SENTENCE_END.split(line):
            words = re.findall(r"[A-Za-z]{2,}", sentence)
            if len(words) >= 5:
                statements.append(sentence)
    return statements


def compute_trust(
    answer: str,
    *,
    cited_texts: list[str],
    facts_text: str = "",
    question: str = "",
    extractive: bool = False,
) -> TrustResult:
    """Score an answer (0–100) by how much of it is backed by the inputs.

    ``answer`` should be the model's text only — without the property-fact
    header or the guidance notice the backend adds.
    """
    if extractive:
        # Fallback reply: clauses quoted straight from the database.
        return TrustResult(
            score=100,
            level="high",
            reasons=["Policy text quoted directly — no AI-written summary"],
        )

    source_numbers = {
        _as_number(n) for n in _figures(" ".join([*cited_texts, facts_text, question]))
    }

    statements = _statements(answer)
    cited = from_figures = reasoning = 0
    for statement in statements:
        if _CITATION.search(statement):
            cited += 1
            continue
        own = _figures(statement)
        if own and all(_as_number(f) in source_numbers for f in own):
            from_figures += 1
        elif not own:
            reasoning += 1
    total = len(statements)
    coverage = (cited + from_figures + 0.5 * reasoning) / total if total else 0.0
    figures = _figures(answer)
    unsupported = [f for f in figures if _as_number(f) not in source_numbers]
    supported = len(figures) - len(unsupported)
    figure_support = supported / len(figures) if figures else None

    if figure_support is None:
        raw = coverage
    else:
        raw = 0.5 * coverage + 0.5 * figure_support
    score = round(raw * 100)
    if cited == 0:
        score = min(score, 30)  # nothing traceable to a clause

    reasons: list[str] = []
    if total:
        reasons.append(f"{cited} of {total} statements cite a policy clause")
        if from_figures:
            reasons.append(
                f"{from_figures} more {'uses' if from_figures == 1 else 'use'} only figures from the sources"
            )
        if reasoning:
            reasons.append(
                f"{reasoning} {'is' if reasoning == 1 else 'are'} the AI's own reasoning or conclusions"
            )
        unbacked = total - cited - from_figures - reasoning
        if unbacked:
            reasons.append(
                f"{unbacked} {'contains' if unbacked == 1 else 'contain'} figures not found in the sources"
            )
    if figures:
        reasons.append(f"{supported} of {len(figures)} figures found in the cited clauses or property facts")
    if unsupported:
        shown = ", ".join(dict.fromkeys(unsupported[:4]))
        reasons.append(f"Not found in the sources: {shown}")
    if cited == 0:
        reasons.append("The answer cites no policy clauses")

    return TrustResult(
        score=score,
        level=_level(score),
        cited_statements=cited,
        total_statements=total,
        supported_figures=supported,
        total_figures=len(figures),
        unsupported_figures=list(dict.fromkeys(unsupported)),
        reasons=reasons,
    )
