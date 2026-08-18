"use client";

import { useChat } from "@/context/ChatContext";

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
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-[var(--line)] bg-[var(--sidebar)] text-[var(--sidebar-ink)] transition-transform duration-200 lg:static lg:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 border-b border-white/10 px-4 py-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--accent)] text-sm font-bold text-white">
            PA
          </div>
          <div className="min-w-0">
            <p className="font-[family-name:var(--font-display)] text-base leading-tight text-white">
              Planning Advisor
            </p>
            <p className="truncate text-xs text-white/60">
              Shire of Plantagenet
            </p>
          </div>
        </div>

        <div className="p-3">
          <button
            type="button"
            onClick={createSession}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-3 py-2.5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            <span aria-hidden>+</span> New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-3">
          <p className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/45">
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
                    className={`w-full rounded-lg px-3 py-2.5 pr-9 text-left text-sm transition ${
                      active
                        ? "bg-white/12 text-white"
                        : "text-white/75 hover:bg-white/8 hover:text-white"
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

        <div className="border-t border-white/10 p-4 text-xs leading-relaxed text-white/55">
          Guidance only. Not a planning determination or legal advice. Confirm
          with the Shire before acting.
        </div>
      </aside>
    </>
  );
}
