"use client";

import { useChat } from "@/context/ChatContext";
import { useSocket } from "@/context/SocketContext";
import { Sidebar } from "@/components/chat/Sidebar";
import { MessageList } from "@/components/chat/MessageList";
import { Composer } from "@/components/chat/Composer";
import { AddressGateForm } from "@/components/chat/AddressGateForm";
import { PropertyHeader } from "@/components/chat/PropertyHeader";
import { BrandLink, Icon, Spinner } from "@/components/brand/Brand";

function ConnectionBanner() {
  const { isConnected, status, connect } = useSocket();
  const { hydrated } = useChat();
  if (!hydrated || isConnected || status === "idle" || status === "connecting") {
    return null;
  }
  return (
    <div
      role="status"
      className="flex items-center gap-2.5 bg-danger-soft px-4 py-2.5 text-sm text-danger-ink sm:px-9"
    >
      <Icon name="wifi" className="h-[18px] w-[18px] flex-none text-danger" />
      <span className="flex-1">Can’t reach the advisor right now — reconnecting…</span>
      <button
        type="button"
        onClick={connect}
        className="min-h-9 rounded-lg border border-danger px-3 text-[13px] font-semibold"
      >
        Retry
      </button>
    </div>
  );
}

function GateTopBar() {
  const { setSidebarOpen } = useChat();
  return (
    <header className="on-forest flex items-center justify-between gap-3 bg-forest px-3 py-2 text-on-forest sm:px-8 sm:py-3">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open your chats"
          className="inline-flex h-11 w-11 items-center justify-center rounded-xl lg:hidden"
        >
          <Icon name="menu" className="h-[22px] w-[22px]" />
        </button>
        <BrandLink className="lg:hidden" label="Planning Advisor" />
        <span className="hidden text-sm text-on-forest-muted lg:inline">New chat</span>
      </div>
    </header>
  );
}

export function ChatShell() {
  const { activeSession, hydrated } = useChat();
  const ready = Boolean(activeSession?.locationReady);

  return (
    <div className="flex h-dvh overflow-hidden bg-stone text-ink">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        {!hydrated ? (
          <div className="flex flex-1 items-center justify-center gap-3 text-muted" role="status">
            <Spinner className="h-5 w-5" />
            Loading your chats…
          </div>
        ) : ready ? (
          <>
            <PropertyHeader />
            <ConnectionBanner />
            <main className="relative flex min-h-0 flex-1 flex-col">
              <div className="min-h-0 flex-1 overflow-y-auto">
                <MessageList />
              </div>
              <Composer />
            </main>
          </>
        ) : (
          <>
            <GateTopBar />
            <ConnectionBanner />
            <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">
              <AddressGateForm />
            </main>
          </>
        )}
      </div>
    </div>
  );
}
