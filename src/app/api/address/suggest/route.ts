import { NextRequest, NextResponse } from "next/server";
import {
  PLANTAGENET_BOUNDS,
  isPlantagenetSuggestion,
} from "@/lib/plantagenetScope";

export const runtime = "nodejs";

type NominatimItem = {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type?: string;
  class?: string;
  address?: {
    road?: string;
    house_number?: string;
    suburb?: string;
    town?: string;
    city?: string;
    village?: string;
    municipality?: string;
    county?: string;
    state?: string;
    postcode?: string;
    country?: string;
  };
};

type Suggestion = {
  id: string;
  label: string;
  lat?: number;
  lng?: number;
  locality?: string;
  state?: string;
  postcode?: string;
  /** Landgate land_ids of every lot at this address (Landgate results only) */
  landIds?: number[];
  /** How many lots share this address (Landgate results only) */
  lotCount?: number;
  source: "landgate" | "nominatim";
};

/**
 * FastAPI base URL reachable from the Next.js server (not the browser).
 * Docker: ADVISOR_API_URL=http://api:8000. Otherwise derived from the
 * WebSocket URL (ws://host:8000/ws/chat → http://host:8000).
 */
function advisorApiUrl(): string {
  const explicit = process.env.ADVISOR_API_URL?.trim();
  if (explicit) return explicit.replace(/\/+$/, "");
  const ws = process.env.NEXT_PUBLIC_WS_URL?.trim();
  if (ws) {
    try {
      const url = new URL(ws);
      url.protocol = url.protocol === "wss:" ? "https:" : "http:";
      return url.origin;
    } catch {
      // fall through
    }
  }
  return "http://127.0.0.1:8000";
}

/**
 * Exact street-number / lot search from Landgate's cadastre (via FastAPI).
 * Returns null when the service is unreachable so we can fall back.
 */
async function landgateSuggestions(q: string): Promise<Suggestion[] | null> {
  try {
    const res = await fetch(
      `${advisorApiUrl()}/api/address/search?q=${encodeURIComponent(q)}&limit=8`,
      { cache: "no-store", signal: AbortSignal.timeout(9000) },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as {
      results?: Array<Omit<Suggestion, "source">>;
    };
    return (data.results ?? []).map((item) => ({
      id: item.id,
      label: item.label,
      lat: item.lat,
      lng: item.lng,
      locality: item.locality,
      state: item.state,
      landIds: item.landIds,
      lotCount: item.lotCount,
      source: "landgate" as const,
    }));
  } catch {
    return null;
  }
}

/**
 * Address suggestions for the Shire of Plantagenet.
 *
 * 1. Landgate cadastre addresses (exact house / lot number → exact lot)
 * 2. OpenStreetMap Nominatim fallback (towns, roads, places without a number)
 *
 * Backend also re-checks via live SLIP LGA when chat starts.
 */
export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";

  if (q.length < 3) {
    return NextResponse.json({
      source: "nominatim",
      attribution: "© OpenStreetMap contributors",
      scope: "Shire of Plantagenet only",
      results: [],
    });
  }

  const landgate = await landgateSuggestions(q);
  if (landgate && landgate.length > 0) {
    return NextResponse.json({
      source: "landgate",
      attribution: "Address data © Landgate",
      scope: "Shire of Plantagenet only",
      results: landgate,
    });
  }

  const params = new URLSearchParams({
    q,
    format: "jsonv2",
    addressdetails: "1",
    countrycodes: "au",
    limit: "12",
    dedupe: "1",
  });

  // Bias toward Shire of Plantagenet (viewbox: left,top,right,bottom)
  params.set(
    "viewbox",
    `${PLANTAGENET_BOUNDS.minLng},${PLANTAGENET_BOUNDS.maxLat},${PLANTAGENET_BOUNDS.maxLng},${PLANTAGENET_BOUNDS.minLat}`,
  );
  params.set("bounded", "1");

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?${params.toString()}`,
      {
        headers: {
          "User-Agent":
            process.env.NOMINATIM_USER_AGENT ??
            "PlantagenetPlanningAdvisor/0.1 (Murdoch ICT620 student project)",
          Accept: "application/json",
        },
        cache: "no-store",
      },
    );

    if (!res.ok) {
      return NextResponse.json(
        {
          source: "nominatim",
          attribution: "© OpenStreetMap contributors",
          scope: "Shire of Plantagenet only",
          error: `Nominatim error ${res.status}`,
          results: [],
        },
        { status: 502 },
      );
    }

    const data = (await res.json()) as NominatimItem[];
    const results: Suggestion[] = data
      .map((item) => {
        const locality =
          item.address?.suburb ||
          item.address?.town ||
          item.address?.city ||
          item.address?.village;
        return {
          id: String(item.place_id),
          label: item.display_name,
          lat: Number(item.lat),
          lng: Number(item.lon),
          locality,
          state: item.address?.state,
          postcode: item.address?.postcode,
          municipality: item.address?.municipality,
          county: item.address?.county,
        };
      })
      .filter((item) =>
        isPlantagenetSuggestion({
          label: item.label,
          lat: item.lat,
          lng: item.lng,
          locality: item.locality,
          postcode: item.postcode,
          municipality: item.municipality,
          county: item.county,
        }),
      )
      .map(
        (item): Suggestion => ({
          id: item.id,
          label: item.label,
          lat: item.lat,
          lng: item.lng,
          locality: item.locality,
          state: item.state,
          postcode: item.postcode,
          source: "nominatim",
        }),
      )
      .slice(0, 8);

    return NextResponse.json({
      source: "nominatim",
      attribution: "© OpenStreetMap contributors",
      scope: "Shire of Plantagenet only",
      results,
    });
  } catch {
    return NextResponse.json(
      {
        source: "nominatim",
        attribution: "© OpenStreetMap contributors",
        scope: "Shire of Plantagenet only",
        error: "Failed to reach Nominatim",
        results: [],
      },
      { status: 502 },
    );
  }
}
