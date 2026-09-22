"use client";

import Link from "next/link";

const TOPICS = [
  {
    title: "Sheds & outbuildings",
    detail: "Size, setbacks, and when approval is needed.",
  },
  {
    title: "Fences & boundaries",
    detail: "Height limits and neighbour considerations.",
  },
  {
    title: "Dwellings & additions",
    detail: "Single houses, extensions, and exemptions.",
  },
] as const;

const STEPS = [
  {
    step: "01",
    title: "Enter your address",
    detail: "We confirm the site is in the Shire of Plantagenet and look up zoning.",
  },
  {
    step: "02",
    title: "Ask in plain language",
    detail: "Describe what you want to build or change — no planning jargon required.",
  },
  {
    step: "03",
    title: "Get cited guidance",
    detail: "Answers draw from local policies and schemes, with sources you can check.",
  },
] as const;

export function HomePage() {
  return (
    <div className="home-page relative min-h-dvh overflow-x-hidden bg-[var(--bg)] text-[var(--ink)]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:shadow-md"
      >
        Skip to content
      </a>

      <header className="home-nav absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:h-[4.5rem] sm:px-6 lg:px-8">
          <Link
            href="/"
            className="group flex items-center gap-3 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            <span
              className="brand-mark flex h-10 w-10 items-center justify-center rounded-xl text-sm font-bold tracking-wide text-white transition group-hover:scale-[1.03]"
              aria-hidden
            >
              PA
            </span>
            <span className="hidden text-left sm:block">
              <span className="block font-[family-name:var(--font-display)] text-[15px] font-semibold leading-tight tracking-tight text-white drop-shadow-sm">
                Plantagenet
              </span>
              <span className="block text-[11px] font-medium uppercase tracking-[0.14em] text-white/75">
                Planning Advisor
              </span>
            </span>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2" aria-label="Primary">
            <Link
              href="/coverage"
              className="rounded-xl px-3 py-2 text-sm font-semibold text-white/85 transition hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            >
              Coverage
            </Link>
            <Link
              href="/chat"
              className="md-btn-filled rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[var(--accent-deep)] shadow-[0_4px_14px_rgba(0,0,0,0.18)] transition hover:bg-[var(--accent-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--accent-deep)]"
            >
              Start chat
            </Link>
          </nav>
        </div>
      </header>

      <main id="main">
        {/* Hero — one composition: brand, headline, support, CTAs, landscape plane */}
        <section
          className="home-hero relative min-h-[100svh] overflow-hidden"
          aria-labelledby="home-brand"
        >
          <div className="home-hero-media absolute inset-0" aria-hidden>
            <LandscapeBackdrop />
          </div>
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[rgba(8,28,18,0.94)] via-[rgba(10,36,22,0.45)] to-[rgba(12,40,24,0.2)]"
            aria-hidden
          />

          <div className="absolute inset-x-0 top-[max(5.5rem,18vh)] z-10 px-4 sm:px-6 lg:px-8">
            <div className="home-hero-copy mx-auto w-full max-w-6xl">
              <p
                id="home-brand"
                className="home-reveal font-[family-name:var(--font-display)] text-[2rem] font-semibold leading-[1.1] tracking-tight text-white sm:text-4xl md:text-5xl lg:text-[3.5rem]"
              >
                Plantagenet Planning Advisor
              </p>
              <h1 className="home-reveal home-reveal-delay-1 mt-3 max-w-2xl text-base font-semibold leading-snug text-white/95 sm:mt-4 sm:text-xl md:text-[1.35rem]">
                Clear answers on what you can build on your property.
              </h1>
              <p className="home-reveal home-reveal-delay-2 mt-2 max-w-xl text-sm leading-relaxed text-white/78 sm:mt-3 sm:text-base">
                AI guidance grounded in Shire of Plantagenet schemes and local
                planning policies — with citations you can verify.
              </p>

              <div className="home-reveal home-reveal-delay-3 mt-6 flex flex-col gap-3 sm:mt-7 sm:flex-row sm:items-center">
                <Link
                  href="/chat"
                  className="md-btn-filled inline-flex h-11 items-center justify-center rounded-xl bg-white px-6 text-sm font-semibold text-[var(--accent-deep)] shadow-[0_10px_28px_rgba(0,0,0,0.28)] transition hover:bg-[var(--accent-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--accent-deep)] sm:h-12 sm:px-7 sm:text-[15px]"
                >
                  Ask a planning question
                </Link>
                <Link
                  href="/coverage"
                  className="inline-flex h-11 items-center justify-center rounded-xl border border-white/45 bg-white/12 px-5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80 sm:h-12 sm:px-6 sm:text-[15px]"
                >
                  See what&apos;s covered
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* How it works — one job */}
        <section
          className="relative border-t border-[var(--line)] bg-[var(--surface)]"
          aria-labelledby="how-heading"
        >
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent-deep)]">
              How it works
            </p>
            <h2
              id="how-heading"
              className="mt-2 max-w-xl font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-[var(--ink)] sm:text-4xl"
            >
              From address to cited advice in three steps.
            </h2>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-[var(--muted)] sm:text-lg">
              Built for residents and builders who need a fast first read before
              speaking with the Shire.
            </p>

            <ol className="mt-12 grid gap-8 sm:grid-cols-3 sm:gap-6 lg:gap-10">
              {STEPS.map((item) => (
                <li key={item.step} className="relative">
                  <span
                    className="font-[family-name:var(--font-display)] text-4xl font-semibold tabular-nums text-[var(--accent-soft)]"
                    aria-hidden
                  >
                    {item.step}
                  </span>
                  <h3 className="mt-3 text-lg font-semibold tracking-tight text-[var(--ink)]">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
                    {item.detail}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Topics — interactive entry points (surfaces, not hero cards) */}
        <section
          className="relative border-t border-[var(--line)] bg-[var(--panel)]"
          aria-labelledby="topics-heading"
        >
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent-deep)]">
              Common questions
            </p>
            <h2
              id="topics-heading"
              className="mt-2 max-w-xl font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-[var(--ink)] sm:text-4xl"
            >
              Start with what you&apos;re planning.
            </h2>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-[var(--muted)] sm:text-lg">
              Open the advisor and ask about your site — these are typical
              starting points.
            </p>

            <ul className="mt-10 grid gap-4 sm:grid-cols-3">
              {TOPICS.map((topic) => (
                <li key={topic.title}>
                  <Link
                    href="/chat"
                    className="md-surface group flex h-full flex-col rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-[var(--shadow-soft)] transition duration-200 hover:-translate-y-0.5 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow-lift)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
                  >
                    <span className="text-base font-semibold tracking-tight text-[var(--ink)] group-hover:text-[var(--accent-deep)]">
                      {topic.title}
                    </span>
                    <span className="mt-2 flex-1 text-sm leading-relaxed text-[var(--muted)]">
                      {topic.detail}
                    </span>
                    <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--accent)]">
                      Ask in chat
                      <span
                        className="transition group-hover:translate-x-0.5"
                        aria-hidden
                      >
                        →
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Closing CTA */}
        <section
          className="relative overflow-hidden border-t border-[var(--line)]"
          aria-labelledby="cta-heading"
        >
          <div
            className="absolute inset-0"
            aria-hidden
            style={{
              background:
                "linear-gradient(135deg, var(--accent-deep) 0%, #157a49 48%, var(--accent) 100%)",
            }}
          />
          <div
            className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-white/10 blur-2xl"
            aria-hidden
          />
          <div className="relative mx-auto flex max-w-6xl flex-col items-start gap-6 px-4 py-16 sm:flex-row sm:items-end sm:justify-between sm:px-6 sm:py-20 lg:px-8">
            <div className="max-w-xl">
              <h2
                id="cta-heading"
                className="font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-white sm:text-4xl"
              >
                Ready to check your property?
              </h2>
              <p className="mt-3 text-base leading-relaxed text-white/80 sm:text-lg">
                Enter an address in the Shire and ask your first question in
                under a minute.
              </p>
            </div>
            <Link
              href="/chat"
              className="md-btn-filled inline-flex h-12 shrink-0 items-center justify-center rounded-xl bg-white px-7 text-[15px] font-semibold text-[var(--accent-deep)] shadow-[0_8px_24px_rgba(0,0,0,0.2)] transition hover:bg-[var(--accent-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--accent-deep)]"
            >
              Open the advisor
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p className="font-medium text-[var(--ink-soft)]">
            Plantagenet Planning Advisor
          </p>
          <p className="max-w-md sm:text-right">
            Guidance only — not a formal planning decision. Always confirm with
            the Shire of Plantagenet for statutory advice.
          </p>
        </div>
      </footer>
    </div>
  );
}

function LandscapeBackdrop() {
  return (
    <svg
      className="home-landscape h-full w-full object-cover"
      viewBox="0 0 1440 900"
      preserveAspectRatio="xMidYMid slice"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Rolling hills and farmland of the Plantagenet region"
    >
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0.2" y2="1">
          <stop offset="0%" stopColor="#7eb8a0" />
          <stop offset="45%" stopColor="#4a9a72" />
          <stop offset="100%" stopColor="#1f6b48" />
        </linearGradient>
        <linearGradient id="hillFar" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2d7a55" />
          <stop offset="100%" stopColor="#1a5c3d" />
        </linearGradient>
        <linearGradient id="hillNear" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1f9a5c" />
          <stop offset="100%" stopColor="#0f5c36" />
        </linearGradient>
        <linearGradient id="field" x1="0" y1="0" x2="1" y2="0.4">
          <stop offset="0%" stopColor="#c9a45c" stopOpacity="0.55" />
          <stop offset="50%" stopColor="#8fbc8f" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#3d8f62" stopOpacity="0.5" />
        </linearGradient>
      </defs>

      <rect width="1440" height="900" fill="url(#sky)" />

      {/* Soft sun / haze */}
      <circle cx="1180" cy="160" r="90" fill="#fff6d6" opacity="0.35" />
      <circle cx="1180" cy="160" r="160" fill="#ffe8a3" opacity="0.12" />

      {/* Distant ranges */}
      <path
        d="M0 520 C180 460 320 500 480 470 C640 440 760 400 920 430 C1080 460 1240 420 1440 450 L1440 900 L0 900 Z"
        fill="url(#hillFar)"
        opacity="0.85"
      />
      <path
        d="M0 580 C220 520 400 560 560 530 C740 490 880 540 1040 510 C1200 480 1320 520 1440 500 L1440 900 L0 900 Z"
        fill="url(#hillNear)"
      />
      <path
        d="M0 680 C160 640 300 700 460 660 C620 620 780 690 960 650 C1120 620 1280 670 1440 640 L1440 900 L0 900 Z"
        fill="url(#field)"
      />

      {/* Tree silhouettes */}
      <g fill="#0a3d28" opacity="0.55">
        <ellipse cx="180" cy="640" rx="18" ry="36" />
        <ellipse cx="210" cy="655" rx="14" ry="28" />
        <ellipse cx="980" cy="600" rx="22" ry="42" />
        <ellipse cx="1015" cy="615" rx="16" ry="30" />
        <ellipse cx="1240" cy="630" rx="20" ry="38" />
      </g>

      {/* Subtle cadastral / map lines — planning cue without clutter */}
      <g stroke="rgba(255,255,255,0.12)" strokeWidth="1" fill="none">
        <path d="M120 720 L340 700 L520 740 L700 710 L920 750 L1140 720 L1320 745" />
        <path d="M280 760 L480 780 L660 750 L860 790 L1080 760" />
      </g>
    </svg>
  );
}
