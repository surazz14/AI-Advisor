"use client";

import type { ReactNode } from "react";
import { useChat } from "@/context/ChatContext";
import { formatLotArea, shortAddress, type PropertyFacts } from "@/types/chat";
import { Contours, Icon } from "@/components/brand/Brand";

type Chip = { key: string; label: ReactNode; tone?: "warn" };

function factChips(facts: PropertyFacts): Chip[] {
  const chips: Chip[] = [];
  if (facts.zone) {
    chips.push({ key: "zone", label: <><strong>{titleCase(facts.zone)}</strong> zone</> });
  }
  if (facts.rCode) {
    chips.push({ key: "rcode", label: <>R-Code <strong>{facts.rCode}</strong></> });
  }
  const lot = formatLotArea(facts.lotAreaM2);
  if (lot) {
    chips.push(
      facts.lotCount && facts.lotCount > 1
        ? { key: "lot", label: <>{facts.lotCount} lots <strong>≈ {lot}</strong></> }
        : { key: "lot", label: <>Lot <strong>≈ {lot}</strong></> },
    );
  }
  if (Array.isArray(facts.heritage)) {
    chips.push(
      facts.heritage.length === 0
        ? { key: "heritage", label: "No heritage listing" }
        : { key: "heritage", label: <strong>Heritage listed</strong>, tone: "warn" },
    );
  }
  if (typeof facts.bushfireProne === "boolean") {
    chips.push(
      facts.bushfireProne
        ? { key: "bushfire", label: <strong>Bushfire-prone area</strong>, tone: "warn" }
        : { key: "bushfire", label: "Not bushfire-prone" },
    );
  }
  return chips;
}

function titleCase(text: string) {
  // SLIP returns zones in mixed case ("RESIDENTIAL", "Rural Residential")
  if (text !== text.toUpperCase()) return text;
  return text.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Forest header with the confirmed address and live lot facts. */
export function PropertyHeader() {
  const { activeSession, resetLocation, setSidebarOpen, isSending } = useChat();
  if (!activeSession) return null;
  const facts = activeSession.propertyFacts;
  const chips = factChips(facts);

  return (
    <header className="on-forest relative overflow-hidden bg-forest text-on-forest">
      <Contours variant="band" />
      <div className="relative flex flex-col gap-3 px-4 pb-4 pt-3 sm:gap-3.5 sm:px-9 sm:pb-6 sm:pt-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-1">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open your chats"
              className="-ml-2 inline-flex h-11 w-11 flex-none items-center justify-center rounded-xl lg:hidden"
            >
              <Icon name="menu" className="h-[22px] w-[22px]" />
            </button>
            <div className="min-w-0 pt-1 lg:pt-0">
              <p className="text-[13px] font-medium text-on-forest-muted">Your property</p>
              <h1
                className="line-clamp-2 font-display text-[23px] font-medium leading-tight sm:line-clamp-1 sm:text-[34px]"
                title={facts.address}
              >
                {shortAddress(facts.address) || "Selected property"}
              </h1>
            </div>
          </div>
          <button
            type="button"
            onClick={resetLocation}
            disabled={isSending}
            className="inline-flex min-h-11 flex-none items-center gap-2 rounded-full border border-forest-edge px-3.5 text-sm font-medium transition hover:bg-white/10 disabled:opacity-50"
          >
            <Icon name="pin" className="h-4 w-4" />
            <span className="hidden sm:inline">Change address</span>
            <span className="sm:hidden">Change</span>
          </button>
        </div>
        {chips.length > 0 && (
          <ul
            className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-0.5 sm:mx-0 sm:flex-wrap sm:px-0"
            aria-label="Property facts"
          >
            {chips.map((chip) => (
              <li
                key={chip.key}
                className={`flex-none whitespace-nowrap rounded-full px-3 py-1.5 text-[13px] sm:text-sm ${
                  chip.tone === "warn" ? "bg-warn-soft text-warn-ink" : "bg-on-forest text-ink"
                }`}
              >
                {chip.label}
              </li>
            ))}
          </ul>
        )}
      </div>
    </header>
  );
}
