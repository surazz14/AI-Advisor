/** Shared chat WebSocket message protocol (frontend ↔ FastAPI) */

export type ClientSocketEvent =
  | {
      type: "chat.send";
      sessionId: string;
      content: string;
      address?: string;
      lat?: number;
      lng?: number;
      /** Landgate land_ids of every lot at the picked address, when known */
      landIds?: number[];
    }
  | {
      type: "session.hello";
      sessionId: string;
      address?: string;
      lat?: number;
      lng?: number;
      /** Landgate land_ids of every lot at the picked address, when known */
      landIds?: number[];
    };

export type Citation = {
  doc: string;
  clause?: string;
  quote?: string;
  page?: string;
  url?: string;
  topic?: string;
  location?: string;
};

export type HeritageListing = {
  kind:
    | "state_register"
    | "heritage_list"
    | "heritage_area"
    | "local_heritage_survey"
    | "aboriginal_register"
    | "aboriginal_lodged";
  label: string;
  placeName?: string;
  placeNo?: string;
  url?: string;
};

/** How much of an answer is backed by the cited clauses (computed by the backend). */
export type TrustScore = {
  /** 0–100 */
  score: number;
  /** high ≥ 75 (green), medium 50–74 (amber), low < 50 (red) */
  level: "high" | "medium" | "low";
  citedStatements: number;
  totalStatements: number;
  supportedFigures: number;
  totalFigures: number;
  unsupportedFigures?: string[];
  reasons?: string[];
};

export type ZoneInfo = {
  zone: string;
  zoneNumber?: number;
  labelDescription?: string | null;
  schemeName?: string | null;
  schemeNumber?: string | null;
  lga?: string | null;
  gazettalDate?: number | null;
};

export type ServerSocketEvent =
  | {
      type: "chat.assistant";
      sessionId: string;
      content: string;
      /** Client event this answers (absent on older backends) */
      replyTo?: "session.hello" | "chat.send";
      citations?: Citation[];
      zone?: ZoneInfo;
      /** Approximate lot / site area (m²) from Landgate cadastre */
      lotAreaM2?: number;
      /** Lots combined into lotAreaM2 (absent = single lot) */
      lotCount?: number;
      /** R-Code density coding, e.g. "R10" or dual "R10/17.5" */
      rCode?: string;
      /** Heritage listings on the lot ([] = none found; absent = unknown) */
      heritage?: HeritageListing[];
      /** Inside a mapped Bush Fire Prone Area (absent = unknown) */
      bushfireProne?: boolean;
      /** Grounding of the answer in its sources (absent for welcome messages) */
      trust?: TrustScore;
    }
  | {
      type: "chat.error";
      sessionId?: string;
      message: string;
    }
  | {
      type: "session.ready";
      sessionId: string;
    };

export type SocketStatus = "idle" | "connecting" | "connected" | "disconnected" | "error";
