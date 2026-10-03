"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { HeroAddressForm } from "@/components/chat/AddressGateForm";
import { BrandLink, Contours, Icon } from "@/components/brand/Brand";

const STEPS = [
  {
    title: "Pick your address",
    detail:
      "We confirm it’s in the Shire and look up the zone, lot size, R-Code, heritage listings and bushfire map.",
  },
  {
    title: "Ask like you’d ask a neighbour",
    detail: "“Can I put a shed out the back?” works fine. No planning jargon needed.",
  },
  {
    title: "Read the answer and its sources",
    detail:
      "Every answer links to the policy it came from, so you can check it or take it to the Shire.",
  },
] as const;

const TOPICS = [
  {
    title: "Sheds & outbuildings",
    detail: "Size limits, setbacks and shipping containers.",
    ask: "Can I put up a shed without development approval?",
  },
  {
    title: "Fences & boundaries",
    detail: "Front fence heights, dividing fences, pool barriers.",
    ask: "How high can my front fence be?",
  },
  {
    title: "Houses & granny flats",
    detail: "Ancillary dwellings, transportables, exemptions.",
    ask: "Can I add a granny flat to my property?",
  },
  {
    title: "Water tanks, dams & stormwater",
    detail: "Tank sizes, dam setbacks, on-site retention.",
    ask: "What size water tank can I install without approval?",
  },
  {
    title: "Bushfire",
    detail: "Bushfire-prone areas, BAL ratings and what they change.",
    ask: "Is my lot bushfire prone, and what does that change?",
  },
  {
    title: "Tourism & farm stays",
    detail: "B&Bs, chalets, holiday houses and child care.",
    ask: "Can I run a B&B or holiday house on my property?",
  },
] as const;

const LOT_FACTS = [
  { label: "Planning zone", detail: "Residential, Rural, Rural Residential…" },
  { label: "R-Code density", detail: "Where housing density coding applies" },
  { label: "Lot area", detail: "Measured from the Landgate cadastre" },
  { label: "Heritage & bushfire", detail: "Heritage listings and bushfire-prone map" },
] as const;

const SOURCES = [
  "Local Planning Scheme No. 5",
  "Local Planning Policies 1–8",
  "Residential Design Codes",
  "SPP 3.7 Bushfire",
  "Clause 61 Deemed Provisions",
] as const;

function askHref(question: string) {
  return `/chat?ask=${encodeURIComponent(question)}`;
}

export function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-dvh bg-stone text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-paper focus:px-3 focus:py-2"
      >
        Skip to content
      </a>

      <header className="on-forest relative overflow-hidden bg-forest text-on-forest">
        <Contours variant="hero" />
        <div className="relative mx-auto flex max-w-[1180px] flex-col gap-14 px-4 pb-16 pt-4 sm:gap-[72px] sm:px-8 sm:pb-[88px] sm:pt-5">
          <nav className="flex flex-wrap items-center justify-between gap-3" aria-label="Main">
            <BrandLink />
            <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
              <Link
                href="/coverage"
                className="hidden min-h-11 items-center px-3.5 text-[15px] font-medium sm:inline-flex"
              >
                What it covers
              </Link>
              <Link
                href="/chat"
                className="inline-flex min-h-11 items-center rounded-full bg-on-forest px-[18px] text-[15px] font-semibold text-forest transition hover:bg-white"
              >
                Start a chat
              </Link>
            </div>
          </nav>

          <div className="flex max-w-[760px] flex-col gap-5 sm:gap-[22px]">
            <p className="text-[13px] font-semibold tracking-[0.04em] text-on-forest-muted sm:text-[15px]">
              FOR MOUNT BARKER, KENDENUP, NARRIKUP, PORONGURUP &amp; ROCKY GULLY
            </p>
            <h1 className="font-display text-[44px] font-medium leading-[1.02] tracking-[-0.015em] sm:text-[68px]">
              What can I build on my land?
            </h1>
            <p className="max-w-[620px] text-[17px] leading-relaxed text-on-forest-soft sm:text-xl">
              Ask in plain words about sheds, fences, granny flats or water tanks. Answers are
              based on the Shire’s planning policies and checked against your actual lot — with
              the sources shown.
            </p>
            <div className="mt-2.5">
              <HeroAddressForm onStarted={() => router.push("/chat")} />
            </div>
            <p className="text-sm text-on-forest-muted">
              Free · no sign-up · guidance only, not a formal planning decision
            </p>
          </div>
        </div>
      </header>

      <main id="main">
        <section className="mx-auto max-w-[1180px] px-4 pb-16 pt-16 sm:px-8 sm:pb-[72px] sm:pt-[88px]" aria-labelledby="how">
          <h2 id="how" className="font-display text-[32px] font-medium tracking-[-0.01em] sm:text-[42px]">
            Three steps, about a minute
          </h2>
          <ol className="mt-10 grid gap-9 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step.title} className="flex flex-col gap-2.5 border-t border-line pt-5">
                <span className="font-display text-[40px] leading-none text-accent">{i + 1}</span>
                <h3 className="text-[21px] font-semibold">{step.title}</h3>
                <p className="text-[17px] leading-relaxed text-muted">{step.detail}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="bg-stone-deep" aria-labelledby="topics">
          <div className="mx-auto max-w-[1180px] px-4 py-16 sm:px-8 sm:py-20">
            <h2 id="topics" className="font-display text-[32px] font-medium tracking-[-0.01em] sm:text-[42px]">
              What people ask about
            </h2>
            <p className="mt-2.5 text-lg text-muted">Tap one to start with that question.</p>
            <ul className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {TOPICS.map((topic) => (
                <li key={topic.title}>
                  <Link
                    href={askHref(topic.ask)}
                    className="group flex h-full min-h-[132px] flex-col gap-2 rounded-[18px] border border-line bg-paper p-[22px] transition hover:border-accent"
                  >
                    <span className="text-xl font-semibold">{topic.title}</span>
                    <span className="text-base leading-normal text-muted">{topic.detail}</span>
                    <span className="mt-auto inline-flex items-center gap-1.5 pt-1 text-[15px] font-semibold text-accent">
                      Ask
                      <Icon name="arrow" className="h-4 w-4 transition group-hover:translate-x-0.5" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section
          className="mx-auto flex max-w-[1180px] flex-wrap items-center gap-12 px-4 py-16 sm:px-8 sm:py-20"
          aria-labelledby="checks"
        >
          <div className="min-w-0 flex-[1_1_380px]">
            <h2 id="checks" className="font-display text-[32px] font-medium tracking-[-0.01em] sm:text-[42px]">
              Answers that know your lot
            </h2>
            <p className="mt-3.5 text-lg leading-relaxed text-muted">
              Before answering, the advisor looks up your property on the WA government’s
              public maps, so the rules it quotes are the ones that apply to you.
            </p>
          </div>
          <ul className="grid min-w-0 flex-[1_1_460px] grid-cols-1 gap-3.5 sm:grid-cols-2">
            {LOT_FACTS.map((fact) => (
              <li key={fact.label} className="rounded-2xl border border-line bg-paper p-5">
                <div className="font-display text-[24px] leading-tight">{fact.label}</div>
                <div className="mt-1.5 text-[15px] text-muted">{fact.detail}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="border-y border-line" aria-label="Sources used">
          <div className="mx-auto flex max-w-[1180px] flex-wrap items-center gap-x-7 gap-y-3 px-4 py-7 text-[15px] text-muted sm:px-8">
            <span className="font-semibold text-ink">Built on</span>
            {SOURCES.map((s) => (
              <span key={s}>{s}</span>
            ))}
            <Link href="/coverage" className="font-semibold text-accent hover:underline">
              See full coverage →
            </Link>
          </div>
        </section>

        <section className="mx-auto max-w-[1180px] px-4 py-16 sm:px-8 sm:py-20" aria-labelledby="cta">
          <div className="on-forest relative flex flex-wrap items-center justify-between gap-6 overflow-hidden rounded-[28px] bg-forest p-8 text-on-forest sm:p-14">
            <Contours variant="band" className="opacity-70" />
            <div className="relative max-w-[560px]">
              <h2 id="cta" className="font-display text-[32px] font-medium sm:text-[40px]">
                Got a project in mind?
              </h2>
              <p className="mt-2.5 text-lg text-on-forest-soft">
                Check your property before you spend money on plans.
              </p>
            </div>
            <Link
              href="/chat"
              className="relative inline-flex min-h-14 items-center rounded-full bg-on-forest px-7 text-[17px] font-bold text-forest transition hover:bg-white"
            >
              Check my property
            </Link>
          </div>
        </section>
      </main>

      <footer className="on-bark bg-bark text-[#d9d1c3]">
        <div className="mx-auto flex max-w-[1180px] flex-wrap justify-between gap-x-10 gap-y-4 px-4 py-9 text-[15px] leading-relaxed sm:px-8">
          <div className="max-w-[560px]">
            <p className="font-semibold text-on-forest">Plantagenet Planning Advisor</p>
            <p className="mt-1.5">
              Guidance only — not a formal planning decision. Always confirm with the Shire of
              Plantagenet before you build.
            </p>
          </div>
          <div className="flex flex-wrap gap-5">
            <Link href="/coverage" className="text-on-forest hover:underline">
              What it covers
            </Link>
            <span>Map data © OpenStreetMap contributors, WA SLIP</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
