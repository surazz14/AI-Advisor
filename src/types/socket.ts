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

export type ServerSocketEvent =
  | {
      type: "chat.assistant";
      sessionId: string;
      content: string;
      citations?: Array<{ doc: string; clause?: string; quote?: string }>;
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
