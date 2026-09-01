"use client";

import { useEffect, useState } from "react";

/** Shown while waiting for the backend RAG reply. */
export const LOADING_STATUS_MESSAGES = [
  "Checking your property details and zoning…",
  "Searching planning policies in the database…",
  "Matching the best clauses for your question…",
  "Writing a short answer from those clauses…",
  "Still working — complex answers can take a minute…",
  "Almost done — finishing your reply…",
] as const;

/**
 * First message for 20s, then a new message every 40s.
 */
export function useLoadingStatusMessage(active: boolean): string {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setIndex(0);
      return;
    }

    setIndex(0);
    const timers: ReturnType<typeof setTimeout>[] = [];
    let elapsed = 0;
    let i = 0;

    const scheduleNext = (delayMs: number) => {
      const id = setTimeout(() => {
        i = Math.min(i + 1, LOADING_STATUS_MESSAGES.length - 1);
        setIndex(i);
        elapsed += delayMs;
        // After the first 20s swap, keep rotating every 40s
        if (i < LOADING_STATUS_MESSAGES.length - 1) {
          scheduleNext(40_000);
        }
      }, delayMs);
      timers.push(id);
    };

    // First change after 20 seconds
    scheduleNext(20_000);

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [active]);

  return LOADING_STATUS_MESSAGES[index] ?? LOADING_STATUS_MESSAGES[0];
}
