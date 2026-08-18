"use client";

import { useEffect, useId, useRef, useState } from "react";

export type SelectedAddress = {
  address: string;
  lat?: number;
  lng?: number;
  id?: string;
};

type Suggestion = {
  id: string;
  label: string;
  lat?: number;
  lng?: number;
  locality?: string;
  state?: string;
  postcode?: string;
};

type AddressSearchProps = {
  value: string;
  onChange: (value: string) => void;
  onSelect: (selected: SelectedAddress) => void;
};

export function NominatimAddressSearch({
  value,
  onChange,
  onSelect,
}: AddressSearchProps) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const q = value.trim();
    if (q.length < 3) {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    const controller = new AbortController();
    // Nominatim: keep requests infrequent (policy ~1 req/sec)
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `/api/address/suggest?q=${encodeURIComponent(q)}`,
          { signal: controller.signal },
        );
        if (!res.ok) throw new Error("Suggest failed");
        const data = (await res.json()) as { results?: Suggestion[] };
        setSuggestions(data.results ?? []);
        setOpen(true);
        setActiveIndex(-1);
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setSuggestions([]);
        }
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [value]);

  function choose(item: Suggestion) {
    onChange(item.label);
    onSelect({
      address: item.label,
      lat: item.lat,
      lng: item.lng,
      id: item.id,
    });
    setOpen(false);
    setSuggestions([]);
  }

  return (
    <div className="relative">
      <input
        id="street-address"
        value={value}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        placeholder="Start typing an Australian address…"
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => {
          if (suggestions.length) setOpen(true);
        }}
        onBlur={() => {
          blurTimer.current = setTimeout(() => setOpen(false), 150);
        }}
        onKeyDown={(e) => {
          if (!open || !suggestions.length) return;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActiveIndex((i) => (i + 1) % suggestions.length);
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
          } else if (e.key === "Enter" && activeIndex >= 0) {
            e.preventDefault();
            choose(suggestions[activeIndex]);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
        className="w-full rounded-xl border border-[var(--line)] bg-[var(--panel)] px-3 py-3 text-sm text-[var(--ink)] outline-none ring-[var(--ring)] placeholder:text-[var(--muted)] focus:ring-2"
      />

      {loading && (
        <p className="mt-1 text-xs text-[var(--muted)]">
          Searching OpenStreetMap…
        </p>
      )}

      {open && suggestions.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-xl border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow-soft)]"
          onMouseDown={(e) => e.preventDefault()}
        >
          {suggestions.map((item, index) => (
            <li key={item.id}>
              <button
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                className={`block w-full px-3 py-2.5 text-left text-sm transition ${
                  index === activeIndex
                    ? "bg-[var(--accent-soft)] text-[var(--accent-deep)]"
                    : "text-[var(--ink)] hover:bg-[var(--accent-soft)]"
                }`}
                onClick={() => {
                  if (blurTimer.current) clearTimeout(blurTimer.current);
                  choose(item);
                }}
              >
                <span className="block font-medium">{item.label}</span>
                {(item.locality || item.postcode) && (
                  <span className="mt-0.5 block text-xs text-[var(--muted)]">
                    {[item.locality, item.state, item.postcode]
                      .filter(Boolean)
                      .join(" ")}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && !loading && value.trim().length >= 3 && suggestions.length === 0 && (
        <div className="absolute z-20 mt-1 w-full rounded-xl border border-[var(--line)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--muted)] shadow-[var(--shadow-soft)]">
          No match found. You can still continue with this address or lot number.
        </div>
      )}

    </div>
  );
}
