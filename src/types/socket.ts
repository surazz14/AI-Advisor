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
