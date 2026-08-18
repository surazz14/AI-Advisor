"use client";

import { FormEvent, useState } from "react";
import { useChat } from "@/context/ChatContext";

export function PropertyPanel() {
  const { activeSession, updatePropertyFacts } = useChat();
  const [address, setAddress] = useState("");

  if (!activeSession) return null;

  const facts = activeSession.propertyFacts;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = address.trim();
    if (!trimmed) return;
    // MVP: store typed address in context. Later: geocode + GIS lookup.
    updatePropertyFacts({
      address: trimmed,
      zone: "Rural (demo)",
      bushfireProne: true,
      locality: "Plantagenet (demo)",
    });
    setAddress("");
  }

  return (
    <aside className="hidden w-[300px] shrink-0 flex-col border-l border-[var(--line)] bg-white/70 backdrop-blur xl:flex">
      <div className="border-b border-[var(--line)] px-4 py-4">
        <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
          Property context
        </h2>
        <p className="mt-1 text-xs leading-relaxed text-[var(--muted)]">
          Stored in React Context with your chat. Later this comes from Mapbox
          geocoding + WA GIS layers.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-2 border-b border-[var(--line)] p-4">
        <label className="block text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
          Address
        </label>
        <input
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="e.g. Mount Barker WA"
          className="w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm outline-none ring-[var(--accent)] focus:ring-2"
        />
        <button
          type="submit"
          className="w-full rounded-xl bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white hover:brightness-110"
        >
          Save to chat context
        </button>
      </form>

      <div className="space-y-3 p-4 text-sm">
        <Fact label="Address" value={facts.address ?? "Not set"} />
        <Fact label="Zone" value={facts.zone ?? "—"} />
        <Fact
          label="Bushfire prone"
          value={
            facts.bushfireProne == null
              ? "—"
              : facts.bushfireProne
                ? "Yes"
                : "No"
          }
        />
        <Fact label="Locality" value={facts.locality ?? "—"} />
      </div>
    </aside>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] px-3 py-2.5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-1 text-[var(--ink)]">{value}</p>
    </div>
  );
}
