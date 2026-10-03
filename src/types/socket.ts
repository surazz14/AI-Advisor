/** Shared chat WebSocket message protocol (frontend ↔ FastAPI) */

export type ClientSocketEvent =
  | {
      type: "chat.send";
      sessionId: string;
      content: string;
      address?: string;
      lat?: number;
      lng?: number;
    }
  | {
      type: "session.hello";
      sessionId: string;
      address?: string;
      lat?: number;
      lng?: number;
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
      citations?: Citation[];
      zone?: ZoneInfo;
      /** Approximate lot / site area (m²) from Landgate cadastre */
      lotAreaM2?: number;
      /** R-Code density coding, e.g. "R10" or dual "R10/17.5" */
      rCode?: string;
      /** Heritage listings on the lot ([] = none found; absent = unknown) */
      heritage?: HeritageListing[];
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
