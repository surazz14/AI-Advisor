"use client";

import {
  createContext,
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
      unsubStatus();
      // Keep reconnect behavior while app is mounted; disconnect on unmount.
      client.disconnect();
    };
  }, [client]);

  const value: SocketContextValue = {
    status,
    isConnected: status === "connected",
    wsUrl: client.getUrl(),
    connect: () => client.connect(),
    disconnect: () => client.disconnect(),
    send: (event) => client.send(event),
    subscribe: (listener) => client.onMessage(listener),
  };

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
