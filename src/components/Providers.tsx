"use client";

import { SocketProvider } from "@/context/SocketContext";
import { ChatProvider } from "@/context/ChatContext";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SocketProvider>
      <ChatProvider>{children}</ChatProvider>
    </SocketProvider>
  );
}
