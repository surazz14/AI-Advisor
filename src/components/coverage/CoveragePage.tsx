"use client";

import Link from "next/link";
import {
  AI_IMPROVEMENTS,
  GIS_COVERAGE,
  POLICY_COVERAGE,
  coverageStats,
  type CoverageItem,
  type CoverageStatus,
} from "@/data/coverageChecklist";

function StatusMark({ status }: { status: CoverageStatus }) {
  if (status === "have") {
    return (
      <span
        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#1f9a5c] text-sm font-bold text-white"
        title="In the knowledge base"
        aria-label="Have"
      >
        ✓
      </span>
    );
  }
  if (status === "partial") {
    return (
      <span
        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#e8a23a] text-xs font-bold text-white"
        title="Partial coverage"
        aria-label="Partial"
      >
        ~
      </span>
    );
  }
  return (
    <span
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-[#c5d5cb] bg-white text-sm text-[#8a9e91]"
      title="Not in the knowledge base yet"
      aria-label="Missing"
    >
      ○
    </span>
  );
}

function CoverageList({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: CoverageItem[];
}) {
  const stats = coverageStats(items);
  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-[#14261c]">
            {title}
          </h2>
          <p className="mt-1 text-sm text-[#5d7466]">{subtitle}</p>
        </div>
        <p className="text-xs text-[#5d7466]">
          <span className="font-semibold text-[#1f9a5c]">{stats.have} have</span>
          {" · "}
          <span className="font-semibold text-[#b7791f]">
            {stats.partial} partial
          </span>
          {" · "}
          <span className="font-semibold text-[#6b7f74]">{stats.missing} missing</span>
        </p>
      </div>

      <ul className="mt-5 divide-y divide-[#d9ebe0] overflow-hidden rounded-2xl border border-[#d9ebe0] bg-white/90">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex items-start gap-3 px-4 py-3.5 sm:px-5"
          >
            <StatusMark status={item.status} />
            <div className="min-w-0 flex-1 text-left">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <p className="text-[15px] font-semibold text-[#14261c]">
                  {item.name}
                </p>
                {typeof item.approxChunks === "number" ? (
                  <span className="text-[11px] text-[#7a8f83]">
                    ~{item.approxChunks} chunks
                  </span>
                ) : null}
              </div>
              <p className="mt-0.5 text-sm leading-relaxed text-[#5d7466]">
                {item.detail}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function CoveragePage() {
  const policy = coverageStats(POLICY_COVERAGE);
  const gis = coverageStats(GIS_COVERAGE);
  const aiStats = coverageStats(AI_IMPROVEMENTS);
  const haveTotal = policy.have + gis.have;
  const missTotal = policy.missing + gis.missing;

  return (
    <div className="relative min-h-dvh overflow-hidden bg-[#f7faf8] text-[#14261c]">
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            "radial-gradient(900px 420px at 15% -10%, rgba(31,154,92,0.14), transparent 55%), radial-gradient(800px 380px at 95% 10%, rgba(31,154,92,0.10), transparent 50%)",
        }}
      />

      <header className="relative z-10 flex h-14 items-center justify-between border-b border-[#d9ebe0] bg-white/80 px-4 backdrop-blur-md sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1f9a5c] text-xs font-bold text-white">
            PA
          </span>
          <p className="text-sm font-semibold tracking-tight">
            Plantagenet Planning Advisor
          </p>
        </Link>
        <nav className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/coverage"
            className="hidden text-sm font-medium text-[#1f9a5c] sm:inline"
          >
            Coverage
          </Link>
          <Link
            href="/chat"
            className="rounded-full bg-[#1f9a5c] px-4 py-1.5 text-sm font-medium text-white transition hover:bg-[#17834d]"
          >
            Open chat
          </Link>
        </nav>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#1f9a5c]">
          Knowledge tracker
        </p>
        <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
          What the advisor knows
        </h1>
        <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-[#5d7466]">
          Tick = in the RAG index. Empty = still to collect. Use this page to
          track Shire coverage and the next upgrades that make answers stronger.
        </p>

        <div className="mt-8 grid grid-cols-3 gap-3 sm:gap-4">
          <div className="rounded-2xl border border-[#d9ebe0] bg-white/90 px-4 py-4 text-center">
            <p className="text-2xl font-semibold text-[#1f9a5c]">{haveTotal}</p>
            <p className="mt-1 text-xs text-[#5d7466]">Have</p>
          </div>
          <div className="rounded-2xl border border-[#d9ebe0] bg-white/90 px-4 py-4 text-center">
            <p className="text-2xl font-semibold text-[#b7791f]">
              {policy.partial + gis.partial}
            </p>
            <p className="mt-1 text-xs text-[#5d7466]">Partial</p>
          </div>
          <div className="rounded-2xl border border-[#d9ebe0] bg-white/90 px-4 py-4 text-center">
            <p className="text-2xl font-semibold text-[#5d7466]">{missTotal}</p>
            <p className="mt-1 text-xs text-[#5d7466]">Missing</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-4 text-xs text-[#5d7466]">
          <span className="inline-flex items-center gap-1.5">
            <StatusMark status="have" /> In knowledge base
          </span>
          <span className="inline-flex items-center gap-1.5">
            <StatusMark status="partial" /> Partial
          </span>
          <span className="inline-flex items-center gap-1.5">
            <StatusMark status="missing" /> Not yet
          </span>
        </div>

        <CoverageList
          title="Policy & regulations"
          subtitle="Documents embedded for retrieval (policy_rag → Supabase)."
          items={POLICY_COVERAGE}
        />

        <CoverageList
          title="Property / GIS facts"
          subtitle="Live attributes attached to the user’s address or pin."
          items={GIS_COVERAGE}
        />

        <section className="mt-10">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-[#14261c]">
                Toward a ChatGPT-like Shire advisor
              </h2>
              <p className="mt-1 text-sm text-[#5d7466]">
                Retrieval, reasoning, quality checks, and product polish — tick
                what you already ship.
              </p>
            </div>
            <p className="text-xs text-[#5d7466]">
              <span className="font-semibold text-[#1f9a5c]">
                {aiStats.have} have
              </span>
              {" · "}
              <span className="font-semibold text-[#b7791f]">
                {aiStats.partial} partial
              </span>
              {" · "}
              <span className="font-semibold text-[#6b7f74]">
                {aiStats.missing} missing
              </span>
            </p>
          </div>

          <ul className="mt-5 divide-y divide-[#d9ebe0] overflow-hidden rounded-2xl border border-[#d9ebe0] bg-white/90">
            {AI_IMPROVEMENTS.map((item) => (
              <li
                key={item.id}
                className="flex items-start gap-3 px-4 py-3.5 sm:px-5"
              >
                <StatusMark status={item.status} />
                <div className="min-w-0 flex-1 text-left">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-[15px] font-semibold text-[#14261c]">
                      {item.title}
                    </p>
                    <span className="rounded-full bg-[#eef7f1] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#1f9a5c]">
                      {item.category}
                    </span>
                    <span className="rounded-full bg-[#f4f8f5] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#5d7466]">
                      Effort {item.effort}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm leading-relaxed text-[#5d7466]">
                    {item.why}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <p className="mt-10 text-center text-xs text-[#7a8f83]">
          Update{" "}
          <code className="rounded bg-[#eef7f1] px-1.5 py-0.5 text-[11px]">
            src/data/coverageChecklist.ts
          </code>{" "}
          when you ingest a new CSV or ship an AI upgrade.
        </p>
      </main>
    </div>
  );
}
