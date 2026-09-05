/** Coverage tracker for policy data + AI capability gaps.
 * Update this file when new CSVs are ingested.
 */

export type CoverageStatus = "have" | "missing" | "partial";

export type CoverageItem = {
  id: string;
  name: string;
  status: CoverageStatus;
  detail: string;
  approxChunks?: number;
};

export type ImprovementItem = {
  id: string;
  title: string;
  why: string;
  effort: "S" | "M" | "L";
  status: CoverageStatus;
  category: "retrieval" | "reasoning" | "quality" | "context" | "product";
};

/** Policy / regulatory sources in the RAG index */
export const POLICY_COVERAGE: CoverageItem[] = [
  {
    id: "lps5",
    name: "Local Planning Scheme No. 5 (LPS5)",
    status: "have",
    detail: "Full scheme rules in index (~750 chunks).",
    approxChunks: 752,
  },
  {
    id: "clause61",
    name: "Clause 61 Deemed Provisions (state exemptions)",
    status: "have",
    detail: "Statewide “approval not required” works/use exemptions.",
    approxChunks: 42,
  },
  {
    id: "lpp3",
    name: "LPP3 – Outbuildings & shipping containers",
    status: "have",
    detail: "Sheds, size limits, containers, deemed-to-comply.",
    approxChunks: 18,
  },
  {
    id: "lpp5",
    name: "LPP5 – Local exemptions from development approval",
    status: "have",
    detail: "Local exemption table pack + LPP5 single-house exemptions in non-residential zones.",
    approxChunks: 36,
  },
  {
    id: "lpp6",
    name: "LPP6 – Water tanks",
    status: "have",
    detail: "Tank size/height and deemed-to-comply standards.",
    approxChunks: 9,
  },
  {
    id: "lpp7",
    name: "LPP7 – Stormwater management",
    status: "have",
    detail: "On-site retention and overflow rules (+ brochure notes).",
    approxChunks: 10,
  },
  {
    id: "lpp8",
    name: "LPP8 – Dams & water features",
    status: "have",
    detail: "Dam exemptions, setbacks, assessment criteria.",
    approxChunks: 14,
  },
  {
    id: "fencing",
    name: "Fencing pack (Dividing Fences Act, pool barriers, R-Codes front fence)",
    status: "have",
    detail: "No standalone Shire fencing LPP — state/local mix covered.",
    approxChunks: 24,
  },
  {
    id: "spp37",
    name: "SPP 3.7 / Planning for Bushfire Guidelines",
    status: "have",
    detail: "BAL triggers, exemptions, APZ-related guidance.",
    approxChunks: 27,
  },
  {
    id: "rcodes",
    name: "R-Codes Volume 1 (expanded extract)",
    status: "partial",
    detail:
      "102+ rows incl. setbacks/privacy/height tables — not the entire Volume 1 PDF.",
    approxChunks: 104,
  },
  {
    id: "tps3-pol20",
    name: "TPS3-POL20 – Porongurup Rural Village",
    status: "have",
    detail: "Village design / local policy rules.",
    approxChunks: 121,
  },
  {
    id: "reloc",
    name: "Relocated / transportable dwellings policy",
    status: "have",
    detail: "POL5-RELOC / related relocation rules.",
    approxChunks: 13,
  },
  {
    id: "tpp21",
    name: "TPP21 (water-related)",
    status: "have",
    detail: "Included with water LPP pack.",
    approxChunks: 6,
  },
  {
    id: "lpp1",
    name: "LPP1 – Ancillary dwellings",
    status: "have",
    detail: "Plot ratio 100m², potable water, setbacks, bushfire / effluent rules.",
    approxChunks: 16,
  },
  {
    id: "lpp2",
    name: "LPP2 – Tourism development",
    status: "have",
    detail: "B&B, chalets, holiday house, nature-based parks, unit limits, bushfire BAL refusal.",
    approxChunks: 22,
  },
  {
    id: "lpp4",
    name: "LPP4 – Child care / family day care",
    status: "have",
    detail: "Lot size, parking, hours, outdoor space, BMP where bushfire-prone.",
    approxChunks: 19,
  },
  {
    id: "tpp-other",
    name: "Other TPPs (signs, feedlots, plantations, SCA surrounds, etc.)",
    status: "missing",
    detail: "Add when client demos need those topics.",
  },
  {
    id: "lps5-reserves",
    name: "LPS5 reserve / Environmental conservation schedules",
    status: "missing",
    detail: "Scheme reserve lists still missing. LAA Crown-reserve mechanism (Class A, management bodies) is indexed separately.",
  },
  {
    id: "laa-reserves",
    name: "Land Administration Act – Crown reserve mechanism",
    status: "have",
    detail: "How reserves are created/managed: Class A safeguards, management orders, leases, purpose change.",
    approxChunks: 25,
  },
  {
    id: "heritage",
    name: "Heritage places / heritage overlay list",
    status: "have",
    detail: "74 Plantagenet inHerit places (Municipal + State Register) + Aboriginal Heritage Act rules. Live per-lot GIS flag still separate.",
    approxChunks: 81,
  },
  {
    id: "structure-plans",
    name: "Structure plans (Rural Village / estates)",
    status: "partial",
    detail: "Porongurup TPP18.1 appendix rules + register/expiry notes. Map-only WAPC plan drawings still not fully text-extracted.",
    approxChunks: 24,
  },
  {
    id: "sca-full",
    name: "Special Control Areas — full map + clause pack",
    status: "partial",
    detail: "Some SCA content in LPS5; maps/property flags not fully wired.",
  },
];

/** Live property / GIS attributes the advisor can use */
export const GIS_COVERAGE: CoverageItem[] = [
  {
    id: "zone-live",
    name: "Live planning zone (SLIP ArcGIS)",
    status: "have",
    detail: "Point-in-polygon zone from WA Property & Planning layer.",
  },
  {
    id: "lot-size",
    name: "Lot / site area",
    status: "missing",
    detail: "Needed for shed, tank, and density limits.",
  },
  {
    id: "bushfire-flag",
    name: "Bushfire-prone area flag (DFES map)",
    status: "missing",
    detail: "Yes/no whether SPP 3.7 applies to the lot.",
  },
  {
    id: "bal",
    name: "BAL rating (if assessed)",
    status: "missing",
    detail: "Construction and planning triggers.",
  },
  {
    id: "rcode-density",
    name: "R-Code density (R10 / R20 / …)",
    status: "missing",
    detail: "Drives setbacks, open space, privacy distances.",
  },
  {
    id: "heritage-flag",
    name: "Heritage overlay on property",
    status: "missing",
    detail: "Blocks many deemed exemptions.",
  },
  {
    id: "building-envelope",
    name: "Building envelope",
    status: "missing",
    detail: "Common on Rural Residential / smallholdings lots.",
  },
  {
    id: "services",
    name: "Reticulated water / sewer flags",
    status: "missing",
    detail: "Affects tanks, effluent, stormwater advice.",
  },
];

/** Product / AI capabilities toward a ChatGPT-like Shire advisor */
export const AI_IMPROVEMENTS: ImprovementItem[] = [
  {
    id: "multi-hop",
    title: "Simple multi-hop retrieval",
    why: "Second search fills gaps (e.g. shed + bushfire, or missing Clause 61).",
    effort: "S",
    status: "have",
    category: "retrieval",
  },
  {
    id: "more-context",
    title: "Larger retrieval window (top 10–12 clauses)",
    why: "More policy text in the prompt than the original top-5.",
    effort: "S",
    status: "have",
    category: "context",
  },
  {
    id: "live-zone",
    title: "Live zone in the prompt",
    why: "SLIP zoning is passed into search text and answers.",
    effort: "M",
    status: "have",
    category: "context",
  },
  {
    id: "citations",
    title: "Citation-backed answers",
    why: "Shows source titles, locations, and official links under replies.",
    effort: "S",
    status: "have",
    category: "quality",
  },
  {
    id: "zone-filter",
    title: "Zone-aware retrieval filter",
    why: "Prefer clauses that match the live zone so the wrong schedule is less likely.",
    effort: "M",
    status: "missing",
    category: "retrieval",
  },
  {
    id: "hybrid",
    title: "Hybrid search (vector + keyword)",
    why: "Catch exact terms like “Clause 61”, “LPP3”, “outbuilding” that pure vectors miss.",
    effort: "M",
    status: "missing",
    category: "retrieval",
  },
  {
    id: "rerank",
    title: "Rerank after retrieve",
    why: "Pull 20 candidates, keep the best 8 — closer to production RAG quality.",
    effort: "M",
    status: "missing",
    category: "retrieval",
  },
  {
    id: "query-rewrite",
    title: "Query rewrite before embed",
    why: "Expand “can I build a shed?” into zone + topic keywords for better search.",
    effort: "S",
    status: "partial",
    category: "retrieval",
  },
  {
    id: "plan-retrieve",
    title: "Plan → retrieve → answer",
    why: "LLM lists needed topics first, then runs targeted searches (stronger multi-hop).",
    effort: "M",
    status: "missing",
    category: "reasoning",
  },
  {
    id: "verify",
    title: "Contradiction / verification pass",
    why: "Second LLM check: unsupported claims or conflicting clauses → safer rewrite.",
    effort: "M",
    status: "missing",
    category: "quality",
  },
  {
    id: "claim-ground",
    title: "Claim grounding",
    why: "Every sentence/claim mapped to a retrieved clause ID before showing the answer.",
    effort: "L",
    status: "missing",
    category: "quality",
  },
  {
    id: "safe-template",
    title: "Safe conflict templates",
    why: "If exemption + bushfire/heritage both hit, force “may still need approval if…”.",
    effort: "S",
    status: "missing",
    category: "quality",
  },
  {
    id: "similarity-gate",
    title: "Low-confidence refusal",
    why: "If retrieval scores are weak, say “not enough policy found” instead of guessing.",
    effort: "S",
    status: "partial",
    category: "quality",
  },
  {
    id: "gis-rich",
    title: "Rich property context (lot size, bushfire, heritage, R-density)",
    why: "ChatGPT-like for a shire needs the lot facts, not only zone name.",
    effort: "L",
    status: "missing",
    category: "context",
  },
  {
    id: "history",
    title: "Multi-turn chat memory",
    why: "Follow-ups like “what if it’s bushfire prone?” use the previous question.",
    effort: "S",
    status: "partial",
    category: "product",
  },
  {
    id: "streaming",
    title: "Streaming WebSocket replies",
    why: "Tokens appear live — feels like ChatGPT instead of a long wait.",
    effort: "S",
    status: "missing",
    category: "product",
  },
  {
    id: "eval",
    title: "Golden Q&A evaluation set (20–40 questions)",
    why: "Measure accuracy on sheds, fences, bushfire, exemptions, water.",
    effort: "M",
    status: "missing",
    category: "quality",
  },
  {
    id: "process-faq",
    title: "DA / building permit process FAQ",
    why: "How to apply, fees, timeframes — common “ChatGPT for council” questions.",
    effort: "S",
    status: "missing",
    category: "context",
  },
  {
    id: "https",
    title: "Production HTTPS + wss:// deploy",
    why: "Public hosting without broken sockets (AWS/Docker + TLS).",
    effort: "M",
    status: "missing",
    category: "product",
  },
];

export function coverageStats(items: { status: CoverageStatus }[]) {
  const have = items.filter((i) => i.status === "have").length;
  const partial = items.filter((i) => i.status === "partial").length;
  const missing = items.filter((i) => i.status === "missing").length;
  return { have, partial, missing, total: items.length };
}
