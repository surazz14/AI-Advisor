import type { HeritageListing } from "@/types/socket";

export type MessageRole = "user" | "assistant";

export type Citation = {
  doc: string;
  clause?: string;
  quote?: string;
  page?: string;
  url?: string;
  topic?: string;
  location?: string;
};

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  citations?: Citation[];
  /** "welcome" = first message after the address is confirmed; "error" = could not answer */
  kind?: "welcome" | "error";
};

export type PropertyFacts = {
  address?: string;
  lat?: number;
  lng?: number;
  /** Landgate land_ids of every lot at the address (Landgate picks only) */
  landIds?: number[];
  /** @deprecated single-lot id saved by older sessions — read via landIds */
  landId?: number;
  /** Live facts returned by the backend for this lot */
  zone?: string;
  lotAreaM2?: number;
  /** Lots combined into lotAreaM2 (undefined = single lot) */
  lotCount?: number;
  rCode?: string;
  /** undefined = unknown, [] = checked and none found */
  heritage?: HeritageListing[];
  /** undefined = unknown */
  bushfireProne?: boolean;
};

export type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  propertyFacts: PropertyFacts;
  /** Chat unlocks only after an address is set */
  locationReady: boolean;
  updatedAt: string;
};

export function displayLocation(facts: PropertyFacts): string {
  return facts.address?.trim() || "";
}

const DROP_PARTS =
  /^(shire of .+|city of .+|town of .+|western australia|wa|australia|\d{4})$/i;

/**
 * Shorten a Nominatim display name for headings, e.g.
 * "22, Lowood Road, Mount Barker, Shire of Plantagenet, Western Australia, 6324, Australia"
 * → "22 Lowood Road, Mount Barker".
 */
export function shortAddress(address: string | undefined | null): string {
  const raw = (address || "").trim();
  if (!raw) return "";
  const parts = raw
    .split(",")
    .map((p) => p.trim())
    .filter((p) => p && !DROP_PARTS.test(p));
  if (parts.length === 0) return raw;
  // Join a leading house number with the street ("22" + "Lowood Road")
  if (parts.length > 1 && /^\d+[A-Za-z]?(?:[-–]\d+[A-Za-z]?)?$/.test(parts[0])) {
    parts.splice(0, 2, `${parts[0]} ${parts[1]}`);
  }
  return parts.slice(0, 2).join(", ");
}

/** "1,012 m²" or "4.25 ha" */
export function formatLotArea(m2: number | undefined): string | null {
  if (m2 == null || !Number.isFinite(m2) || m2 <= 0) return null;
  if (m2 >= 10_000) return `${(m2 / 10_000).toFixed(2)} ha`;
  return `${Math.round(m2).toLocaleString("en-AU")} m²`;
}
