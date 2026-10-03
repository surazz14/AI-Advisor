"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useChat } from "@/context/ChatContext";
import { useSocket } from "@/context/SocketContext";
import { shortAddress } from "@/types/chat";
import { BrandLink, Icon } from "@/components/brand/Brand";

export function Sidebar() {
  const {
    sessions,
    activeSessionId,
    isSidebarOpen,
    isSending,
    createSession,
    selectSession,
    deleteSession,
    setSidebarOpen,
  } = useChat();

  // Close the mobile drawer with Escape
  useEffect(() => {
    if (!isSidebarOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isSidebarOpen, setSidebarOpen]);

  const visible = sessions.filter(
    (s) => s.locationReady || s.messages.length > 0 || s.id === activeSessionId,
  );

  return (
    <>
      {isSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-[rgba(43,38,32,0.45)] lg:hidden"
          aria-label="Close your chats"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        aria-label="Your chats"
        className={`on-bark fixed inset-y-0 left-0 z-40 flex w-[300px] max-w-[86vw] flex-col gap-4 bg-bark px-3.5 py-4 text-on-bark transition-transform duration-200 lg:static lg:w-[288px] lg:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between gap-2 pl-1.5">
          <BrandLink label="Planning Advisor" className="text-on-forest" />
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close your chats"
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl lg:hidden"
          >
            <Icon name="close" className="h-5 w-5" />
          </button>
        </div>

        <button
          type="button"
          disabled={isSending}
          onClick={() => {
            createSession();
            setSidebarOpen(false);
          }}
          className="flex min-h-12 items-center gap-2 rounded-xl bg-on-forest px-3.5 text-[15px] font-semibold text-ink transition hover:bg-white disabled:opacity-60"
        >
          <Icon name="plus" className="h-[18px] w-[18px]" />
          New chat
        </button>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <p className="px-1.5 pb-2 text-xs font-semibold tracking-[0.06em] text-on-bark-muted">
            YOUR CHATS
          </p>
          <ul className="flex flex-col gap-0.5">
            {visible.map((session) => {
              const active = session.id === activeSessionId;
              const place = shortAddress(session.propertyFacts.address);
              return (
                <li key={session.id} className="group relative">
                  <button
                    type="button"
                    aria-current={active ? "page" : undefined}
                    disabled={isSending && !active}
                    onClick={() => {
                      selectSession(session.id);
                      setSidebarOpen(false);
                    }}
                    className={`block w-full rounded-xl py-2.5 pl-3 pr-11 text-left transition disabled:opacity-50 ${
                      active ? "bg-bark-raised text-on-forest" : "hover:bg-white/5"
                    }`}
                  >
                    <span className={`block truncate text-[15px] ${active ? "font-semibold" : ""}`}>
                      {session.title}
                    </span>
                    <span className="block truncate text-[13px] text-on-bark-muted">
                      {place || "No address yet"}
                    </span>
                  </button>
                  <button
                    type="button"
                    aria-label={`Delete chat: ${session.title}`}
                    disabled={isSending && active}
                    onClick={() => deleteSession(session.id)}
                    className="absolute right-1.5 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-on-bark-muted opacity-100 transition hover:bg-white/10 hover:text-on-forest focus-visible:opacity-100 disabled:hidden lg:opacity-0 lg:group-hover:opacity-100"
                  >
                    <Icon name="trash" className="h-4 w-4" />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="flex flex-col gap-2 border-t border-bark-line px-1.5 pt-3 text-[13px] leading-relaxed text-on-bark-muted">
          <Link href="/coverage" className="inline-flex min-h-10 items-center text-[15px] text-on-bark hover:text-on-forest">
            What the advisor covers
          </Link>
          <ConnectionStatus />
          <p>Chats are saved on this device only. Guidance only — not a formal planning decision.</p>
        </div>
      </aside>
    </>
  );
}

function ConnectionStatus() {
  const { isConnected } = useSocket();
  return (
    <p className="flex items-center gap-2">
      <span
        className={`h-2 w-2 rounded-full ${isConnected ? "bg-[#8fd16b]" : "bg-[#e8a23a]"}`}
        aria-hidden
      />
      {isConnected ? "Advisor online" : "Advisor offline — reconnecting"}
    </p>
  );
}
