#!/usr/bin/env python3
"""Run the Plantagenet Planning Advisor answer-quality benchmark.

For each benchmark row this script:
  1. resolves the test address with GET /api/address/search (Landgate);
  2. asks the question with POST /api/advisor/ask;
  3. records the answer, the cited documents and the property facts;
  4. checks automatically whether each expected source was cited.

It does NOT decide pass/fail. Reviewers fill in the correctness,
faithfulness, caveats and result columns afterwards (report Section 6.3.3).

Usage (backend running on port 8000):
    python eval_benchmark.py --api http://localhost:8000 \
        --questions benchmark.csv --out results.csv

benchmark.csv columns: id, question, address, expected_sources
  expected_sources: sources separated by ";" — each must be cited.
  Alternatives for one source are separated by "|" (any one counts).
  Matching is a case-insensitive substring match on cited document titles,
  e.g. "Local Planning Policy No. 3" or "Local Planning Policy No. 5|Clause 61".
Rows whose address starts with "REPLACE" are skipped until a real address
is filled in. Only Python's standard library is needed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

REVIEW_COLUMNS = ["correctness", "faithfulness", "caveats", "result", "reviewer", "notes"]


def http_json(url: str, payload: dict | None = None, timeout: int = 180) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method="POST" if data else "GET",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:300]}") from exc


def expected_hits(expected: str, cited_titles: list[str]) -> tuple[bool, list[str]]:
    """Return (all expected sources cited, per-source report)."""
    titles = [t.lower() for t in cited_titles]
    report, all_ok = [], True
    for group in [g.strip() for g in expected.split(";") if g.strip()]:
        options = [o.strip().lower() for o in group.split("|") if o.strip()]
        ok = any(opt in t for opt in options for t in titles)
        all_ok &= ok
        report.append(f"{group}: {'yes' if ok else 'NO'}")
    return all_ok, report


def run(api: str, questions_path: str, out_path: str, delay: float) -> int:
    api = api.rstrip("/")
    with open(questions_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fields = ["id", "question", "address", "resolved_address", "land_ids", "zone",
              "lot_area_m2", "bushfire_prone", "heritage", "answer", "response_seconds", "cited_documents",
              "expected_sources", "expected_cited", "expected_detail", "provider_note",
              *REVIEW_COLUMNS]
    out_rows, cited_ok = [], 0
    for row in rows:
        out = {k: "" for k in fields}
        out.update(id=row["id"], question=row["question"], address=row["address"],
                   expected_sources=row.get("expected_sources", ""))
        if row["address"].strip().upper().startswith("REPLACE"):
            out["provider_note"] = "skipped: test address not filled in"
            out_rows.append(out)
            print(f"{row['id']}: skipped (no test address)")
            continue
        try:
            search = http_json(f"{api}/api/address/search?" + urllib.parse.urlencode({"q": row["address"], "limit": 1}))
            results = search.get("results") or []
            if not results:
                raise RuntimeError("address not found by Landgate search")
            place = results[0]
            out["resolved_address"] = place.get("label", "")
            out["land_ids"] = " ".join(str(i) for i in place.get("landIds") or [])
            started = time.perf_counter()
            reply = http_json(f"{api}/api/advisor/ask", {
                "sessionId": f"eval-{row['id']}-{uuid.uuid4().hex[:8]}",
                "address": place["label"], "lat": place["lat"], "lng": place["lng"],
                "landIds": place.get("landIds"), "question": row["question"],
            })
            elapsed = round(time.perf_counter() - started, 2)
            titles = [c.get("doc", "") for c in reply.get("citations") or []]
            ok, detail = expected_hits(row.get("expected_sources", ""), titles)
            cited_ok += ok
            out.update(
                zone=(reply.get("zone") or {}).get("zone", ""),
                lot_area_m2=reply.get("lotAreaM2", ""),
                bushfire_prone=reply.get("bushfireProne", ""),
                heritage=("; ".join(h.get("label", "") for h in reply["heritage"]) or "none found") if reply.get("heritage") is not None else "unknown",
                answer=reply.get("content", ""),
                response_seconds=elapsed,
                cited_documents=" | ".join(dict.fromkeys(titles)),
                expected_cited="yes" if ok else "no",
                expected_detail="; ".join(detail),
            )
            print(f"{row['id']}: expected source cited = {'yes' if ok else 'NO'}")
        except Exception as exc:  # record and continue
            out["provider_note"] = str(exc)
            print(f"{row['id']}: ERROR {exc}", file=sys.stderr)
        out_rows.append(out)
        time.sleep(delay)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    run_rows = sum(1 for r in out_rows if r["answer"])
    times = sorted(float(r["response_seconds"]) for r in out_rows if r["response_seconds"] != "")
    print(f"\nAnswered {run_rows}/{len(out_rows)}; expected source cited in {cited_ok}/{run_rows}.")
    if times:
        print(f"Response time: median {times[len(times) // 2]:.1f} s, max {times[-1]:.1f} s.")
    print(f"Results written to {out_path}. Reviewers: fill in {', '.join(REVIEW_COLUMNS)}.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--questions", default="benchmark.csv")
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between questions (LLM rate limits)")
    a = ap.parse_args()
    sys.exit(run(a.api, a.questions, a.out, a.delay))
