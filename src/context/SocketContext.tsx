"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getChatSocket } from "@/lib/chatSocket";
import type { ClientSocketEvent, ServerSocketEvent, SocketStatus } from "@/types/socket";

type SocketContextValue = {
  status: SocketStatus;
  isConnected: boolean;
  wsUrl: string;
  connect: () => void;
  disconnect: () => void;
  send: (event: ClientSocketEvent) => void;
  subscribe: (listener: (event: ServerSocketEvent) => void) => () => void;
};

const SocketContext = createContext<SocketContextValue | null>(null);

export function SocketProvider({ children }: { children: ReactNode }) {
  const client = useMemo(() => getChatSocket(), []);
  const [status, setStatus] = useState<SocketStatus>(client.getStatus());

  useEffect(() => {
    const unsubStatus = client.onStatus(setStatus);
    client.connect();
    return () => {
      // Keep the singleton socket alive across React Strict Mode remounts
      // and page navigations. Only unsubscribe this provider's listener.
      unsubStatus();
    };
  }, [client]);

  const connect = useCallback(() => client.connect(), [client]);
  const disconnect = useCallback(() => client.disconnect(), [client]);
  const send = useCallback(
    (event: ClientSocketEvent) => client.send(event),
    [client],
  );
  const subscribe = useCallback(
    (listener: (event: ServerSocketEvent) => void) => {
      const unsubscribe = client.onMessage(listener);
      return () => {
        unsubscribe();
      };
    },
    [client],
  );

  const value = useMemo<SocketContextValue>(
    () => ({
      status,
      isConnected: status === "connected",
      wsUrl: client.getUrl(),
      connect,
      disconnect,
      send,
      subscribe,
    }),
    [client, connect, disconnect, send, status, subscribe],
  );

  return (
    <SocketContext.Provider value={value}>{children}</SocketContext.Provider>
  );
}

export function useSocket() {
  const ctx = useContext(SocketContext);
  if (!ctx) {
    throw new Error("useSocket must be used within SocketProvider");
  }
  return ctx;
}
