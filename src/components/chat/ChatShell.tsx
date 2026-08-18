"use client";

import { useChat } from "@/context/ChatContext";
import { Sidebar } from "@/components/chat/Sidebar";
import { MessageList } from "@/components/chat/MessageList";
import { Composer } from "@/components/chat/Composer";
import { PropertyPanel } from "@/components/chat/PropertyPanel";

export function ChatShell() {
  const { setSidebarOpen, activeSession } = useChat();

  return (
    <div className="flex h-dvh overflow-hidden bg-[var(--bg)] text-[var(--ink)]">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[var(--line)] bg-white/70 px-4 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-sm lg:hidden"
            >
              Menu
            </button>
            <div>
              <h1 className="font-[family-name:var(--font-display)] text-lg leading-none text-[var(--ink)]">
                {activeSession?.title ?? "Planning chat"}
              </h1>
              <p className="mt-1 text-xs text-[var(--muted)]">
                ChatGPT-style advisor · context saved locally
              </p>
            </div>
          </div>
          <div className="hidden rounded-full border border-[var(--line)] bg-[var(--panel)] px-3 py-1 text-xs text-[var(--muted)] sm:block">
            Demo UI · RAG coming next
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1">
          <div className="app-grid absolute inset-0 opacity-40" aria-hidden />
          <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
            <div className="min-h-0 flex-1 overflow-y-auto">
              <MessageList />
            </div>
            <Composer />
          </main>
          <PropertyPanel />
        </div>
      </div>
    </div>
  );
}
