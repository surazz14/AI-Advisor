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
import { Contours, Icon, Spinner } from "@/components/brand/Brand";

type PickedAddress = {
  address: string;
  lat: number;
  lng: number;
  landIds?: number[];
  source?: SelectedAddress["source"];
};
type Picked = PickedAddress | null;

/** Shared address picking + validation for the hero and the chat gate. */
function useAddressPicker(
  start: (input: PickedAddress) => Promise<void>,
  onStarted?: () => void,
) {
  const [address, setAddress] = useState("");
  const [picked, setPicked] = useState<Picked>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function onChange(value: string) {
    setAddress(value);
    if (picked && value !== picked.address) setPicked(null);
    if (error) setError("");
  }

  function onSelect(selected: SelectedAddress) {
    setAddress(selected.address);
    if (selected.lat != null && selected.lng != null) {
      setPicked({
        address: selected.address,
        lat: selected.lat,
        lng: selected.lng,
        landIds: selected.landIds,
        source: selected.source,
      });
    }
    setError("");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    if (!address.trim()) {
      setError("Enter your property address to continue.");
      return;
    }
    if (!picked) {
      setError("Please choose your address from the list of suggestions.");
      return;
    }
    // Landgate matches are exact lots inside the Shire bbox; OSM picks also
    // need town/postcode evidence. The backend confirms the LGA either way.
    const textOk =
      picked.source === "landgate" ||
      isPlantagenetSuggestion({ label: picked.address, lat: picked.lat, lng: picked.lng });
    if (!textOk || !coordsLookLikePlantagenet(picked.lat, picked.lng)) {
      setError(OUTSIDE_SHIRE_MESSAGE);
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await start(picked);
      onStarted?.();
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? err.message
          : "We couldn’t check this address. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return { address, picked, error, submitting, onChange, onSelect, onSubmit };
}

function ErrorBox({ id, message }: { id: string; message: string }) {
  return (
    <div
      id={id}
      role="alert"
      className="flex gap-3 rounded-2xl bg-danger-soft p-4 text-left text-[15px] leading-relaxed text-danger-ink"
    >
      <Icon name="alert" className="mt-0.5 h-[22px] w-[22px] flex-none text-danger" />
      <span>{message}</span>
    </div>
  );
}

/** Full-page address step shown in /chat before the conversation starts. */
export function AddressGateForm() {
  const { startChatWithAddress } = useChat();
  const picker = useAddressPicker((input) => startChatWithAddress(input));
  const errorId = "address-error";

  return (
    <div className="relative flex flex-1 justify-center overflow-hidden px-4 py-10 sm:px-8 sm:py-16">
      <Contours variant="light" />
      <form
        onSubmit={picker.onSubmit}
        className="relative flex w-full max-w-[640px] flex-col gap-5"
        noValidate
      >
        <p className="text-sm font-semibold tracking-[0.04em] text-accent">STEP 1 OF 2</p>
        <h1 className="font-display text-[34px] font-medium leading-[1.06] tracking-[-0.01em] sm:text-[52px]">
          Which property is this about?
        </h1>
        <p className="text-[17px] leading-relaxed text-muted sm:text-lg">
          Type your house or lot number and street, then choose your address
          from the list so we can find your exact lot.
          The advisor covers the Shire of Plantagenet only.
        </p>

        <div className="flex flex-col gap-2">
          <label htmlFor="street-address" className="text-[15px] font-semibold">
            Property address
          </label>
          <NominatimAddressSearch
            value={picker.address}
            onChange={picker.onChange}
            onSelect={picker.onSelect}
            invalid={Boolean(picker.error)}
            describedBy={picker.error ? errorId : undefined}
            disabled={picker.submitting}
          />
          {picker.picked && !picker.error && (
            <p className="flex items-center gap-2 text-sm text-accent">
              <Icon name="check" className="h-4 w-4" />
              Address selected
            </p>
          )}
        </div>

        {picker.error && <ErrorBox id={errorId} message={picker.error} />}

        <button
          type="submit"
          disabled={picker.submitting}
          className="inline-flex min-h-14 items-center justify-center gap-2.5 self-start rounded-full bg-accent px-7 text-[17px] font-bold text-white transition hover:bg-accent-hover disabled:cursor-wait disabled:opacity-80"
        >
          {picker.submitting ? (
            <>
              <Spinner className="h-[18px] w-[18px]" />
              Looking up your lot…
            </>
          ) : (
            <>
              Check this property
              <Icon name="arrow" className="h-[18px] w-[18px]" />
            </>
          )}
        </button>

        <div className="flex gap-3.5 rounded-2xl bg-stone-deep p-4 text-[15px] leading-relaxed text-[#3f382f]">
          <Icon name="info" className="mt-0.5 h-[22px] w-[22px] flex-none" />
          <span>
            {picker.submitting
              ? "Checking the zone, lot size, R-Code, heritage listings and bushfire map for this lot. This takes a few seconds."
              : "Next we’ll look up the zone, lot size, R-Code, heritage listings and bushfire map for this lot."}
          </span>
        </div>
      </form>
    </div>
  );
}

/** Compact address search used in the home page hero. */
export function HeroAddressForm({ onStarted }: { onStarted: () => void }) {
  const { startNewChatWithAddress } = useChat();
  const picker = useAddressPicker((input) => startNewChatWithAddress(input), onStarted);
  const errorId = "hero-address-error";

  return (
    <form onSubmit={picker.onSubmit} className="flex w-full max-w-[640px] flex-col gap-3" noValidate>
      <label htmlFor="hero-address" className="sr-only">
        Your property address
      </label>
      <div className="flex flex-col gap-2 rounded-[28px] bg-paper p-2 text-ink sm:flex-row sm:items-center sm:rounded-full sm:pl-5">
        <div className="flex min-w-0 flex-1 items-center gap-2.5 px-3 sm:px-0">
          <Icon name="pin" className="h-5 w-5 flex-none text-muted" />
          <NominatimAddressSearch
            inputId="hero-address"
            variant="hero"
            value={picker.address}
            onChange={picker.onChange}
            onSelect={picker.onSelect}
            invalid={Boolean(picker.error)}
            describedBy={picker.error ? errorId : undefined}
            disabled={picker.submitting}
          />
        </div>
        <button
          type="submit"
          disabled={picker.submitting}
          className="inline-flex min-h-[52px] flex-none items-center justify-center gap-2 rounded-full bg-accent px-6 text-base font-semibold text-white transition hover:bg-accent-hover disabled:cursor-wait disabled:opacity-80"
        >
          {picker.submitting ? (
            <>
              <Spinner className="h-4 w-4" />
              Checking…
            </>
          ) : (
            "Check my property"
          )}
        </button>
      </div>
      {picker.error && <ErrorBox id={errorId} message={picker.error} />}
    </form>
  );
}
