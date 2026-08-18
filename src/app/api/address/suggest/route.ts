import { NextRequest, NextResponse } from "next/server";

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
};

/**
 * Address suggestions via OpenStreetMap Nominatim.
 * Policy: https://operations.osmfoundation.org/policies/nominatim/
 * - Identify the app with a User-Agent
 * - Keep request volume low (we debounce on the client)
 * - Show OSM attribution in the UI
 */
export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";

  if (q.length < 3) {
    return NextResponse.json({
      source: "nominatim",
      attribution: "© OpenStreetMap contributors",
      results: [],
    });
  }

  const params = new URLSearchParams({
    q,
    format: "jsonv2",
    addressdetails: "1",
    countrycodes: "au",
    limit: "8",
    dedupe: "1",
  });

  // Bias toward southern WA / Plantagenet region (viewbox: left,top,right,bottom)
  params.set("viewbox", "116.8,-34.2,118.3,-35.0");
  params.set("bounded", "0");

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?${params.toString()}`,
      {
        headers: {
          // Required by Nominatim usage policy — identify your app + contact
          "User-Agent":
            process.env.NOMINATIM_USER_AGENT ??
            "PlantagenetPlanningAdvisor/0.1 (Murdoch ICT620 student project)",
          Accept: "application/json",
        },
        // Avoid Next fetch caching of live search
        cache: "no-store",
      },
    );

    if (!res.ok) {
      return NextResponse.json(
        {
          source: "nominatim",
          attribution: "© OpenStreetMap contributors",
          error: `Nominatim error ${res.status}`,
          results: [],
        },
        { status: 502 },
      );
    }

    const data = (await res.json()) as NominatimItem[];
    const results: Suggestion[] = data.map((item) => {
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
      };
    });

    return NextResponse.json({
      source: "nominatim",
      attribution: "© OpenStreetMap contributors",
      results,
    });
  } catch {
    return NextResponse.json(
      {
        source: "nominatim",
        attribution: "© OpenStreetMap contributors",
        error: "Failed to reach Nominatim",
        results: [],
      },
      { status: 502 },
    );
  }
}
