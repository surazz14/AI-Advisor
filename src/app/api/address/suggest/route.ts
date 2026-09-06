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
};

/**
 * Address suggestions via OpenStreetMap Nominatim.
 * Hard-scoped to Shire of Plantagenet (town/postcode checks).
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
      .map(({ municipality: _m, county: _c, ...rest }) => rest)
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
