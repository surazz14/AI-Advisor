import Link from "next/link";
import {
  AI_IMPROVEMENTS,
  GIS_COVERAGE,
  POLICY_COVERAGE,
  coverageStats,
  type CoverageItem,
  type CoverageStatus,
  type ImprovementItem,
} from "@/data/coverageChecklist";
import { BrandLink } from "@/components/brand/Brand";

const STATUS_TEXT: Record<CoverageStatus, string> = {
  have: "Covered",
  partial: "Partly covered",
  missing: "Not yet",
};

/** Status icon — each status has its own shape, not just its own colour. */
function StatusMark({ status, size = 22 }: { status: CoverageStatus; size?: number }) {
  if (status === "have") {
    return (
      <svg width={size} height={size} viewBox="0 0 20 20" className="flex-none" aria-hidden>
        <circle cx="10" cy="10" r="9" fill="#3e6b4f" />
        <path d="M6 10.5l2.5 2.5 5.5-6" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (status === "partial") {
    return (
      <svg width={size} height={size} viewBox="0 0 20 20" className="flex-none" aria-hidden>
        <circle cx="10" cy="10" r="8" fill="none" stroke="#9a5a1f" strokeWidth="2" />
        <path d="M10 2a8 8 0 0 1 0 16z" fill="#9a5a1f" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" className="flex-none" aria-hidden>
      <circle cx="10" cy="10" r="8" fill="none" stroke="#6b6255" strokeWidth="2" strokeDasharray="3 2.5" />
    </svg>
  );
}

function StatusTag({
  status,
  labels = STATUS_TEXT,
}: {
  status: CoverageStatus;
  labels?: Record<CoverageStatus, string>;
}) {
  if (status === "have") return <span className="sr-only">({labels.have})</span>;
  return (
    <span className={`text-sm font-medium ${status === "partial" ? "text-warn-ink" : "text-muted"}`}>
      {" "}
      · {labels[status].toLowerCase()}
    </span>
  );
}

const ROADMAP_TEXT: Record<CoverageStatus, string> = {
  have: "Done",
  partial: "In progress",
  missing: "Planned",
};

function CoverageRows({ items }: { items: CoverageItem[] }) {
  return (
    <ul className="border-t border-line">
      {items.map((item) => (
        <li key={item.id} className="grid grid-cols-[28px_minmax(0,1fr)] gap-3.5 border-b border-line py-3.5">
          <span className="pt-0.5">
            <StatusMark status={item.status} />
          </span>
          <div>
            <p className="text-[17px] font-semibold">
              {item.name}
              <StatusTag status={item.status} />
            </p>
            <p className="text-[15px] leading-relaxed text-muted">{item.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

const EFFORT_TEXT: Record<ImprovementItem["effort"], string> = {
  S: "Small",
  M: "Medium",
  L: "Large",
};

function RoadmapRows({ items }: { items: ImprovementItem[] }) {
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {items.map((item) => (
        <li key={item.id} className="flex gap-3.5 rounded-2xl border border-line bg-paper p-[18px]">
          <span className="pt-0.5">
            <StatusMark status={item.status} />
          </span>
          <div className="min-w-0">
            <p className="text-[16px] font-semibold leading-snug">
              {item.title}
              <StatusTag status={item.status} labels={ROADMAP_TEXT} />
            </p>
            <p className="mt-1 text-[15px] leading-relaxed text-muted">{item.why}</p>
            <p className="mt-2 text-[13px] text-muted">
              Effort: {EFFORT_TEXT[item.effort]} · {item.category}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function CoveragePage() {
  const policy = coverageStats(POLICY_COVERAGE);
  const gis = coverageStats(GIS_COVERAGE);
  const ai = coverageStats(AI_IMPROVEMENTS);

  const stats = [
    { value: policy.have, label: "policy sources fully covered" },
    { value: policy.partial, label: "partly covered" },
    { value: policy.missing, label: "not covered yet" },
  ];

  return (
    <div className="min-h-dvh bg-stone text-ink">
      <header className="on-forest bg-forest text-on-forest">
        <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-8 sm:py-4">
          <BrandLink />
          <Link
            href="/chat"
            className="inline-flex min-h-11 items-center rounded-full bg-on-forest px-[18px] text-[15px] font-semibold text-forest transition hover:bg-white"
          >
            Start a chat
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-[1180px] flex-col gap-11 px-4 pb-20 pt-12 sm:px-8 sm:pt-14">
        <div className="max-w-[720px]">
          <h1 className="font-display text-[40px] font-medium leading-[1.05] tracking-[-0.01em] sm:text-[54px]">
            What the advisor knows
          </h1>
          <p className="mt-3.5 text-[17px] leading-relaxed text-muted sm:text-[19px]">
            The documents it reads from and the facts it looks up about your lot. If a topic
            isn’t covered yet, it should say so instead of guessing.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3.5 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-[18px] border border-line bg-paper p-5 sm:p-[22px]">
              <div className="font-display text-[40px] leading-none sm:text-[44px]">{s.value}</div>
              <div className="mt-1.5 text-[15px] text-muted">{s.label}</div>
            </div>
          ))}
          <div className="rounded-[18px] bg-forest p-5 text-on-forest sm:p-[22px]">
            <div className="font-display text-[40px] leading-none sm:text-[44px]">{gis.have}</div>
            <div className="mt-1.5 text-[15px] text-on-forest-soft">live facts checked for your lot</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-2.5 text-[15px]" aria-label="Legend">
          {(["have", "partial", "missing"] as const).map((status) => (
            <span key={status} className="inline-flex items-center gap-2">
              <StatusMark status={status} size={20} />
              {STATUS_TEXT[status]}
            </span>
          ))}
        </div>

        <div className="flex flex-wrap items-start gap-10">
          <section className="min-w-0 flex-[999_1_560px]" aria-labelledby="policies">
            <h2 id="policies" className="mb-3.5 font-display text-[30px] font-medium sm:text-[32px]">
              Policies &amp; regulations
            </h2>
            <CoverageRows items={POLICY_COVERAGE} />
          </section>

          <aside className="flex min-w-0 flex-[1_1_340px] flex-col gap-6">
            <section className="rounded-[20px] border border-line bg-paper p-6" aria-labelledby="facts">
              <h2 id="facts" className="font-display text-[28px] font-medium">
                Facts about your lot
              </h2>
              <p className="mb-3.5 mt-1.5 text-[15px] text-muted">
                Looked up live from WA government maps.
              </p>
              <ul className="flex flex-col gap-3">
                {GIS_COVERAGE.map((item) => (
                  <li key={item.id} className="flex items-start gap-2.5 text-[16px]">
                    <span className="pt-0.5">
                      <StatusMark status={item.status} size={20} />
                    </span>
                    <span className={item.status === "have" ? "" : "text-muted"}>
                      {item.name}
                      <StatusTag status={item.status} />
                    </span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-[20px] bg-stone-deep p-6 text-[16px] leading-relaxed">
              <h2 className="mb-1.5 text-lg font-bold">Missing something?</h2>
              <p>
                If your question isn’t covered, the advisor will tell you and point you to the
                Shire’s planning team.
              </p>
            </section>
          </aside>
        </div>

        <section aria-labelledby="roadmap">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 id="roadmap" className="font-display text-[30px] font-medium sm:text-[32px]">
                Improvements to the advisor
              </h2>
              <p className="mt-1.5 text-[15px] text-muted">
                Retrieval, reasoning, quality checks and product polish.
              </p>
            </div>
            <p className="text-[15px] text-muted">
              {ai.have} done · {ai.partial} in progress · {ai.missing} planned
            </p>
          </div>
          <RoadmapRows items={AI_IMPROVEMENTS} />
        </section>
      </main>

      <footer className="on-bark bg-bark text-[#d9d1c3]">
        <div className="mx-auto max-w-[1180px] px-4 py-8 text-[15px] sm:px-8">
          Guidance only — not a formal planning decision. Always confirm with the Shire of
          Plantagenet before you build.
        </div>
      </footer>
    </div>
  );
}
