"use client";

import { useEffect, useState } from "react";

/** Shown while waiting for the backend reply, in the order the work happens. */
export const LOADING_STATUS_MESSAGES = [
  "Reading your question…",
  "Searching the Shire’s planning policies…",
  "Matching the rules to your lot…",
  "Writing your answer…",
  "Still working — detailed answers can take up to a minute…",
  "Almost done…",
] as const;

const STEP_DELAYS_MS = [2500, 6000, 9000, 20000, 30000];

/**
 * Index of the current loading step. Mount the component that uses this
 * only while a reply is pending — it starts from step 0 on every mount.
 */
export function useLoadingStep(): number {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    let elapsed = 0;
    STEP_DELAYS_MS.forEach((delay, i) => {
      elapsed += delay;
      timers.push(setTimeout(() => setIndex(i + 1), elapsed));
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  return Math.min(index, LOADING_STATUS_MESSAGES.length - 1);
}
