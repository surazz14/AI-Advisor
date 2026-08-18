"use client";

import { ChatProvider } from "@/context/ChatContext";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return <ChatProvider>{children}</ChatProvider>;
}
