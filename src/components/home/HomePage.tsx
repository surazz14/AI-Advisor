"use client";

import Link from "next/link";

const SUGGESTIONS = [
  "Can I build a shed?",
  "Fence height rules",
  "Do I need approval?",
];

export function HomePage() {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-hidden bg-[#f7faf8] text-[#14261c]">
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            "radial-gradient(900px 420px at 15% -10%, rgba(31,154,92,0.14), transparent 55%), radial-gradient(800px 380px at 95% 10%, rgba(31,154,92,0.10), transparent 50%), radial-gradient(700px 420px at 50% 110%, rgba(31,154,92,0.08), transparent 55%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(rgba(20,38,28,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(20,38,28,0.035) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage:
            "radial-gradient(ellipse at center, black 35%, transparent 80%)",
        }}
      />

      <header className="relative z-10 flex h-14 items-center justify-between border-b border-[#d9ebe0] bg-white/80 px-4 backdrop-blur-md sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1f9a5c] text-xs font-bold text-white">
            PA
          </span>
          <p className="text-sm font-semibold tracking-tight">
            Plantagenet Planning Advisor
          </p>
        </div>
        <Link
          href="/chat"
          className="rounded-full bg-[#1f9a5c] px-4 py-1.5 text-sm font-medium text-white transition hover:bg-[#17834d]"
        >
          Try
        </Link>
      </header>

      <main className="relative z-10 flex flex-1 flex-col items-center justify-center px-4 pb-20 text-center">
        <div className="w-full max-w-xl rounded-[28px] border border-[#d9ebe0] bg-white/90 p-8 shadow-[0_18px_50px_rgba(20,38,28,0.08)] backdrop-blur-sm sm:p-10">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-[#1f9a5c] text-lg font-bold text-white shadow-[0_10px_24px_rgba(31,154,92,0.28)]">
            PA
          </div>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            What can I help with?
          </h1>
          <p className="mx-auto mt-3 max-w-md text-[15px] leading-relaxed text-[#5d7466]">
            Ask about sheds, fences, dwellings and setbacks for properties in
            the Shire of Plantagenet.
          </p>

          <Link
            href="/chat"
            className="mt-8 flex w-full items-center justify-between rounded-2xl border border-[#d9ebe0] bg-[#f4f8f5] px-5 py-4 text-left text-[15px] text-[#7a8f83] transition hover:border-[#1f9a5c]/40 hover:bg-[#eef7f1]"
          >
            <span>Ask a planning question…</span>
            <span className="rounded-full bg-[#1f9a5c] px-3 py-1 text-xs font-semibold text-white">
              Start
            </span>
          </Link>

          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map((label) => (
              <Link
                key={label}
                href="/chat"
                className="rounded-full border border-[#d9ebe0] bg-white px-3.5 py-1.5 text-xs text-[#3f5a4a] transition hover:border-[#1f9a5c]/50 hover:bg-[#f3faf6]"
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      </main>

      <footer className="relative z-10 px-4 py-4 text-center text-[11px] text-[#7a8f83]">
        Guidance only — not a formal planning decision.
      </footer>
    </div>
  );
}
