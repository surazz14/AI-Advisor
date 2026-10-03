"use client";

import { useEffect, useId, useRef, useState } from "react";
import { isPlantagenetSuggestion } from "@/lib/plantagenetScope";
import { Icon, Spinner } from "@/components/brand/Brand";

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
  inputId?: string;
  /** "page" = bordered field; "hero" = borderless field inside a pill */
  variant?: "page" | "hero";
  invalid?: boolean;
  describedBy?: string;
  disabled?: boolean;
};

const MIN_CHARS = 3;

/** Split "22, Lowood Road, Mount Barker, …" into a main line and a detail line. */
function splitLabel(label: string) {
  const parts = label.split(",").map((p) => p.trim()).filter(Boolean);
  if (parts.length > 1 && /^\d+[A-Za-z]?(?:[-–]\d+[A-Za-z]?)?$/.test(parts[0])) {
    parts.splice(0, 2, `${parts[0]} ${parts[1]}`);
  }
  const main = parts[0] ?? label;
  const rest = parts
    .slice(1)
    .filter((p) => !/^(australia|western australia)$/i.test(p))
    .slice(0, 3)
    .join(", ");
  return { main, rest };
}

export function NominatimAddressSearch({
  value,
  onChange,
  onSelect,
  inputId = "street-address",
  variant = "page",
  invalid = false,
  describedBy,
  disabled = false,
}: AddressSearchProps) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [resultsFor, setResultsFor] = useState("");
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  // Label of the suggestion just picked — no need to search for it again.
  const [chosen, setChosen] = useState("");
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const query = value.trim();
  const searchable = query.length >= MIN_CHARS && query !== chosen.trim();
  const shown = searchable && resultsFor === query ? suggestions : [];
  const isOpen = open && searchable && !disabled;
  const showEmpty =
    isOpen && !loading && resultsFor === query && shown.length === 0;

  useEffect(() => {
    if (!searchable || disabled) return;

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `/api/address/suggest?q=${encodeURIComponent(query)}`,
          { signal: controller.signal },
        );
        if (!res.ok) throw new Error("Suggest failed");
        const data = (await res.json()) as { results?: Suggestion[] };
        const scoped = (data.results ?? []).filter((item) =>
          isPlantagenetSuggestion({
            label: item.label,
            lat: item.lat,
            lng: item.lng,
            locality: item.locality,
            postcode: item.postcode,
          }),
        );
        setSuggestions(scoped);
        setResultsFor(query);
        setFailed(false);
        setActiveIndex(-1);
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setSuggestions([]);
          setResultsFor(query);
          setFailed(true);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 450);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query, searchable, disabled]);

  useEffect(
    () => () => {
      if (blurTimer.current) clearTimeout(blurTimer.current);
    },
    [],
  );

  function cancelClose() {
    if (blurTimer.current) {
      clearTimeout(blurTimer.current);
      blurTimer.current = null;
    }
  }

  function choose(item: Suggestion) {
    setChosen(item.label);
    onChange(item.label);
    onSelect({
      address: item.label,
      lat: item.lat,
      lng: item.lng,
      id: item.id,
    });
    setOpen(false);
  }

  const fieldClass =
    variant === "hero"
      ? "flex items-center gap-2.5"
      : `flex items-center gap-2.5 rounded-2xl border-2 bg-paper px-4 transition ${
          invalid
            ? "border-danger"
            : isOpen
              ? "border-accent"
              : "border-line-strong focus-within:border-accent"
        }`;

  return (
    <div className="relative min-w-0 flex-1">
      <div className={fieldClass}>
        {variant === "page" && <Icon name="pin" className="h-5 w-5 flex-none text-muted" />}
        <input
          id={inputId}
          value={value}
          role="combobox"
          aria-expanded={isOpen}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          aria-activedescendant={
            isOpen && activeIndex >= 0 ? `${listId}-opt-${activeIndex}` : undefined
          }
          autoComplete="off"
          spellCheck={false}
          disabled={disabled}
          placeholder="Start typing your address…"
          onChange={(e) => {
            cancelClose();
            onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            cancelClose();
            setOpen(true);
          }}
          onBlur={() => {
            blurTimer.current = setTimeout(() => setOpen(false), 150);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setOpen(false);
              return;
            }
            if (!isOpen || !shown.length) return;
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActiveIndex((i) => (i + 1) % shown.length);
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setActiveIndex((i) => (i <= 0 ? shown.length - 1 : i - 1));
            } else if (e.key === "Enter" && activeIndex >= 0) {
              e.preventDefault();
              choose(shown[activeIndex]);
            }
          }}
          className="min-h-14 w-full min-w-0 flex-1 bg-transparent text-[17px] text-ink outline-none placeholder:text-muted disabled:cursor-not-allowed sm:text-lg"
          style={{ outline: "none" }}
        />
        {loading && (
          <span className="flex items-center gap-1.5 text-sm text-muted" aria-live="polite">
            <Spinner className="h-4 w-4" />
            <span className="hidden sm:inline">Searching…</span>
          </span>
        )}
      </div>

      {isOpen && (shown.length > 0 || showEmpty) && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Matching addresses"
          className="absolute left-0 right-0 top-[calc(100%+6px)] z-30 max-h-80 overflow-auto rounded-2xl border border-line bg-paper p-1.5 text-left text-ink shadow-[0_18px_40px_rgba(43,38,32,0.16)]"
        >
          {shown.map((item, index) => {
            const { main, rest } = splitLabel(item.label);
            const active = index === activeIndex;
            return (
              <li
                key={item.id}
                id={`${listId}-opt-${index}`}
                role="option"
                aria-selected={active}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(item)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`flex cursor-pointer items-start gap-3 rounded-xl px-3.5 py-3 ${
                  active ? "bg-accent-soft" : ""
                }`}
              >
                <Icon
                  name="pin"
                  className={`mt-0.5 h-[18px] w-[18px] flex-none ${active ? "text-accent" : "text-muted"}`}
                />
                <span className="min-w-0">
                  <span className="block font-semibold">{main}</span>
                  {rest && <span className="block truncate text-sm text-muted">{rest}</span>}
                </span>
              </li>
            );
          })}
          {showEmpty && (
            <li className="px-3.5 py-3 text-[15px] text-muted" role="option" aria-selected={false} aria-disabled>
              {failed
                ? "Address search isn’t responding. Please try again in a moment."
                : "No matching addresses in the Shire of Plantagenet. Try the street name and town, e.g. “Lowood Road, Mount Barker”."}
            </li>
          )}
          <li className="px-3.5 pb-1.5 pt-2 text-xs text-muted" aria-hidden>
            Addresses © OpenStreetMap contributors
          </li>
        </ul>
      )}
    </div>
  );
}
