"use client";

import { FormEvent, useState } from "react";
import { useChat } from "@/context/ChatContext";
import {
  NominatimAddressSearch,
  type SelectedAddress,
} from "@/components/chat/NominatimAddressSearch";
import {
  OUTSIDE_SHIRE_MESSAGE,
  coordsLookLikePlantagenet,
  isPlantagenetSuggestion,
} from "@/lib/plantagenetScope";

export function AddressGateForm() {
  const { startChatWithAddress } = useChat();
  const [address, setAddress] = useState("");
  const [coords, setCoords] = useState<{ lat?: number; lng?: number }>({});
  const [selectedFromList, setSelectedFromList] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleAddressSelect(selected: SelectedAddress) {
    setAddress(selected.address);
    setCoords({ lat: selected.lat, lng: selected.lng });
    setSelectedFromList(true);
    setError("");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const value = address.trim();
    if (!value) {
      setError("Enter a property address to continue.");
      return;
    }
    if (!selectedFromList || coords.lat == null || coords.lng == null) {
      setError(
        "Please pick an address from the Shire of Plantagenet suggestions list.",
      );
      return;
    }
    if (
      !isPlantagenetSuggestion({
        label: value,
        lat: coords.lat,
        lng: coords.lng,
      }) ||
      !coordsLookLikePlantagenet(coords.lat, coords.lng)
    ) {
      setError(OUTSIDE_SHIRE_MESSAGE);
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await startChatWithAddress({
        address: value,
        lat: coords.lat,
        lng: coords.lng,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not start chat for this address.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const canStart =
    selectedFromList && coords.lat != null && coords.lng != null && !submitting;

  return (
    <div className="relative flex flex-1 items-center justify-center px-4 py-10">
      <div className="app-grid absolute inset-0 opacity-50" aria-hidden />
      <form
        onSubmit={onSubmit}
        className="glass-panel relative w-full max-w-lg rounded-[28px] p-6 sm:p-8"
      >
        <div
          className="mb-4 inline-flex items-center gap-2 rounded-full bg-[var(--accent-soft)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--accent-deep)]"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
          Before you chat
        </div>
        <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] leading-tight text-[var(--ink)]">
          Enter your property address
        </h2>
        <p className="mt-2 text-sm text-[var(--ink-soft)]">
          This advisor only covers properties in the Shire of Plantagenet.
        </p>
        <div className="mt-6">
          <label
            htmlFor="street-address"
            className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]"
          >
            Property address
          </label>
          <NominatimAddressSearch
            value={address}
            onChange={(value) => {
              setAddress(value);
              setCoords({});
              setSelectedFromList(false);
            }}
            onSelect={handleAddressSelect}
          />
          {coords.lat != null && coords.lng != null && selectedFromList && (
            <p className="mt-2 rounded-lg bg-[var(--highlight-soft)] px-2.5 py-1.5 text-xs text-[var(--ink-soft)]">
              Selected coordinates: {coords.lat.toFixed(5)},{" "}
              {coords.lng.toFixed(5)}
            </p>
          )}
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-700" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!canStart}
          className="mt-6 w-full rounded-xl bg-[var(--accent)] px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(31,154,92,0.32)] transition hover:bg-[var(--accent-hover)] hover:shadow-[0_14px_30px_rgba(31,154,92,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Checking address…" : "Start chat"}
        </button>

        <p className="mt-4 text-center text-[11px] leading-relaxed text-[var(--muted)]">
          Guidance only — not a formal planning decision. Confirm with the Shire
          before acting.
        </p>
      </form>
    </div>
  );
}
