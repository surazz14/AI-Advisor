import type { ClientSocketEvent, ServerSocketEvent, SocketStatus } from "@/types/socket";

type StatusListener = (status: SocketStatus) => void;
type MessageListener = (event: ServerSocketEvent) => void;

const DEFAULT_WS_URL = "ws://localhost:8000/ws/chat";

/**
 * Lightweight browser WebSocket client for planning-advisor chat.
 * Compatible with FastAPI native WebSocket endpoints.
 */
export class ChatSocketClient {
  private socket: WebSocket | null = null;
  private status: SocketStatus = "idle";
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;
  private readonly statusListeners = new Set<StatusListener>();
  private readonly messageListeners = new Set<MessageListener>();

  constructor(private readonly url: string = process.env.NEXT_PUBLIC_WS_URL || DEFAULT_WS_URL) {}

  getStatus() {
    return this.status;
  }

  getUrl() {
    return this.url;
  }

  onStatus(listener: StatusListener) {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  onMessage(listener: MessageListener) {
    this.messageListeners.add(listener);
    return () => this.messageListeners.delete(listener);
  }

  connect() {
    if (typeof window === "undefined") return;
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.shouldReconnect = true;
    this.setStatus("connecting");

    try {
      const socket = new WebSocket(this.url);
      this.socket = socket;

      socket.onopen = () => {
        this.setStatus("connected");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(String(event.data)) as ServerSocketEvent;
          this.messageListeners.forEach((listener) => listener(data));
        } catch {
          this.messageListeners.forEach((listener) =>
            listener({
              type: "chat.error",
              message: "Received an invalid message from the chat server.",
            }),
          );
        }
      };

      socket.onerror = () => {
        this.setStatus("error");
      };

      socket.onclose = () => {
        this.socket = null;
        this.setStatus("disconnected");
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };
    } catch {
      this.setStatus("error");
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
    this.setStatus("disconnected");
  }

  send(event: ClientSocketEvent) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("Chat socket is not connected");
    }
    this.socket.send(JSON.stringify(event));
  }

  isConnected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2500);
  }

  private setStatus(status: SocketStatus) {
    this.status = status;
    this.statusListeners.forEach((listener) => listener(status));
  }
}

let singleton: ChatSocketClient | null = null;

export function getChatSocket() {
  if (!singleton) {
    singleton = new ChatSocketClient();
  }
  return singleton;
}
