/** Shared Shire of Plantagenet address scope helpers (client + server). */

/** Rough bbox — still must pass town/postcode checks (Albany sits just south). */
export const PLANTAGENET_BOUNDS = {
  minLng: 117.15,
  maxLng: 117.95,
  minLat: -34.88,
  maxLat: -34.40,
} as const;

/** Common Shire of Plantagenet postcodes. */
export const PLANTAGENET_POSTCODES = new Set([
  "6323", // Kendenup
  "6324", // Mount Barker
  "6326", // Porongurup / surrounds
  "6397", // Rocky Gully
]);

export const PLANTAGENET_HINTS = [
  "plantagenet",
  "mount barker",
  "mt barker",
  "kendenup",
  "narrikup",
  "porongurup",
  "rocky gully",
] as const;

const EXCLUDED_HINTS = [
  "albany",
  "perth",
  "fremantle",
  "mandurah",
  "bunbury",
  "denmark",
  "denmark wa",
] as const;

export function inPlantagenetBbox(lat: number, lng: number): boolean {
  return (
    lat >= PLANTAGENET_BOUNDS.minLat &&
    lat <= PLANTAGENET_BOUNDS.maxLat &&
    lng >= PLANTAGENET_BOUNDS.minLng &&
    lng <= PLANTAGENET_BOUNDS.maxLng
  );
}

export function textLooksLikePlantagenet(text: string): boolean {
  const haystack = text.toLowerCase();
  return PLANTAGENET_HINTS.some((hint) => haystack.includes(hint));
}

export function textLooksOutsidePlantagenet(text: string): boolean {
  const haystack = text.toLowerCase();
  // Allow "Albany Highway, Mount Barker" — exclude only clear out-of-shire places
  const hasPlantagenet = textLooksLikePlantagenet(haystack);
  if (hasPlantagenet) return false;
  return EXCLUDED_HINTS.some((hint) => haystack.includes(hint));
}

export function postcodeLooksLikePlantagenet(
  postcode: string | undefined | null,
): boolean {
  if (!postcode) return false;
  return PLANTAGENET_POSTCODES.has(postcode.trim());
}

export function coordsLookLikePlantagenet(
  lat: number | undefined,
  lng: number | undefined,
): boolean {
  if (lat == null || lng == null) return false;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
  return inPlantagenetBbox(lat, lng);
}

/**
 * Strict check for Nominatim suggestions.
 * Require Plantagenet town/name/postcode evidence — bbox alone is not enough
 * (Albany fringe can fall near the box).
 */
export function isPlantagenetSuggestion(input: {
  label: string;
  lat?: number;
  lng?: number;
  locality?: string;
  postcode?: string;
  municipality?: string;
  county?: string;
}): boolean {
  const label = input.label || "";
  if (textLooksOutsidePlantagenet(label)) return false;

  if (postcodeLooksLikePlantagenet(input.postcode)) {
    return coordsLookLikePlantagenet(input.lat, input.lng) || textLooksLikePlantagenet(label);
  }

  if (textLooksLikePlantagenet(label)) {
    // Still require coords inside/near shire when available
    if (input.lat == null || input.lng == null) return true;
    return coordsLookLikePlantagenet(input.lat, input.lng);
  }

  return false;
}

export const OUTSIDE_SHIRE_MESSAGE =
  "This advisor only covers the Shire of Plantagenet. Please choose an address in Mount Barker, Kendenup, Narrikup, Porongurup, or Rocky Gully.";
