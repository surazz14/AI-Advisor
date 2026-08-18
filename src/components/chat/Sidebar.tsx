"use client";

import { useChat } from "@/context/ChatContext";
import { useSocket } from "@/context/SocketContext";

export function Sidebar() {
  const {
    sessions,
    activeSessionId,
    isSidebarOpen,
    createSession,
    selectSession,
    deleteSession,
    setSidebarOpen,
  } = useChat();

  return (
    <>
      {isSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/35 lg:hidden"
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[286px] flex-col border-r border-white/10 text-[var(--sidebar-ink)] transition-transform duration-200 lg:static lg:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{
          background:
            "linear-gradient(180deg, var(--sidebar-elevated) 0%, var(--sidebar) 42%, #0a2218 100%)",
        }}
      >
        <div className="relative overflow-hidden border-b border-white/10 px-4 py-5">
          <div
            className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-[var(--accent)]/25 blur-2xl"
            aria-hidden
          />
          <div className="relative flex items-center gap-3">
            <div className="brand-mark flex h-11 w-11 items-center justify-center rounded-2xl text-sm font-bold text-white">
              PA
            </div>
            <div className="min-w-0">
              <p className="font-[family-name:var(--font-display)] text-[17px] leading-tight text-white">
                Planning Advisor
              </p>
              <p className="truncate text-xs text-emerald-100/65">
                Shire of Plantagenet
              </p>
            </div>
          </div>
        </div>

        <div className="p-3">
          <button
            type="button"
            onClick={createSession}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-3 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(31,154,92,0.35)] transition hover:bg-[var(--accent-hover)]"
          >
            <span aria-hidden>+</span> New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-3">
          <p className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-100/45">
            Conversations
          </p>
          <ul className="space-y-1">
            {sessions.map((session) => {
              const active = session.id === activeSessionId;
              return (
                <li key={session.id} className="group relative">
                  <button
                    type="button"
                    onClick={() => {
                      selectSession(session.id);
                      setSidebarOpen(false);
                    }}
                    className={`w-full rounded-xl px-3 py-2.5 pr-9 text-left text-sm transition ${
                      active
                        ? "bg-white/12 text-white shadow-inner ring-1 ring-white/15"
                        : "text-emerald-50/75 hover:bg-white/8 hover:text-white"
                    }`}
                  >
                    <span className="line-clamp-2">{session.title}</span>
                  </button>
                  <button
                    type="button"
                    aria-label="Delete chat"
                    onClick={() => deleteSession(session.id)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-1.5 py-0.5 text-xs text-white/40 opacity-0 transition hover:bg-white/10 hover:text-white group-hover:opacity-100"
                  >
                    ×
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="border-t border-white/10 bg-black/15 p-4 text-xs leading-relaxed text-emerald-50/60">
          <ConnectionStatus />
          <p className="mt-2">
            Guidance only. Not a planning determination or legal advice. Confirm
            with the Shire before acting.
          </p>
        </div>
      </aside>
    </>
  );
}

function ConnectionStatus() {
  const { isConnected, status } = useSocket();
  return (
    <p className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.12em]">
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          isConnected ? "bg-emerald-400" : "bg-amber-400"
        }`}
        aria-hidden
      />
      <span className={isConnected ? "text-emerald-200/90" : "text-amber-100/80"}>
        {isConnected ? "Live · backend connected" : `Offline · ${status}`}
      </span>
    </p>
  );
}
