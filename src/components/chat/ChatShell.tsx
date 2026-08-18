"use client";

import { useChat } from "@/context/ChatContext";
import { displayLocation } from "@/types/chat";
import { Sidebar } from "@/components/chat/Sidebar";
import { MessageList } from "@/components/chat/MessageList";
import { Composer } from "@/components/chat/Composer";
import { AddressGateForm } from "@/components/chat/AddressGateForm";

export function ChatShell() {
  const { setSidebarOpen, activeSession, resetLocation } = useChat();
  const ready = Boolean(activeSession?.locationReady);
  const locationLabel = activeSession
    ? displayLocation(activeSession.propertyFacts)
    : "";

  return (
    <div className="flex h-dvh overflow-hidden bg-[var(--bg)] text-[var(--ink)]">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-[var(--line)] bg-white/75 px-4 py-3.5 backdrop-blur-md">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-sm lg:hidden"
            >
              Menu
            </button>
            <div className="min-w-0">
              <h1 className="truncate font-[family-name:var(--font-display)] text-lg leading-none text-[var(--ink)]">
                {ready
                  ? activeSession?.title ?? "Planning chat"
                  : "Plantagenet Planning Advisor"}
              </h1>
              <p className="mt-1 truncate text-xs text-[var(--muted)]">
                {ready
                  ? `Address: ${locationLabel}`
                  : "Enter a property address to begin"}
              </p>
            </div>
          </div>

          {ready ? (
            <button
              type="button"
              onClick={resetLocation}
              className="shrink-0 rounded-full border border-[var(--line)] bg-[var(--accent-soft)] px-3 py-1 text-xs text-[var(--accent-deep)] transition hover:border-[var(--accent)]"
            >
              Change address
            </button>
          ) : (
            <div className="hidden rounded-full border border-[var(--line)] bg-[var(--accent-soft)] px-3 py-1 text-xs text-[var(--accent-deep)] sm:block">
              Address required
            </div>
          )}
        </header>

        <div className="relative flex min-h-0 flex-1">
          {!ready ? (
            <AddressGateForm />
          ) : (
            <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
              <div className="app-grid absolute inset-0 opacity-40" aria-hidden />
              <div className="relative min-h-0 flex-1 overflow-y-auto">
                <MessageList />
              </div>
              <Composer />
            </main>
          )}
        </div>
      </div>
    </div>
  );
}
