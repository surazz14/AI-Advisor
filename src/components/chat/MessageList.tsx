"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useChat } from "@/context/ChatContext";
import { useLoadingStatusMessage } from "@/hooks/useLoadingStatusMessage";
import type { ChatMessage, Citation } from "@/types/chat";

function renderContent(content: string) {
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-[var(--ink)]">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      className={`h-4 w-4 shrink-0 text-[var(--muted)] transition-transform duration-200 ease-out ${
        open ? "rotate-180" : "rotate-0"
      }`}
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function CitationItem({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const hasDetail = Boolean(
    citation.quote || citation.location || citation.clause || citation.url,
  );
  const title = citation.topic
    ? `${citation.doc} — ${citation.topic}`
    : citation.doc;

  return (
    <li className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface)]/90">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={hasDetail ? panelId : undefined}
        onClick={() => hasDetail && setOpen((v) => !v)}
        className={`flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition ${
          hasDetail
            ? "hover:bg-[var(--accent-soft)]/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--ring)]"
            : "cursor-default"
        }`}
      >
        <span className="mt-0.5 flex h-5 min-w-5 items-center justify-center rounded-md bg-[var(--accent-soft)] px-1.5 text-[10px] font-bold tabular-nums text-[var(--accent-deep)]">
          {index + 1}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[12.5px] font-semibold leading-snug text-[var(--ink-soft)]">
            {title}
          </span>
          {citation.location && !open && (
            <span className="mt-0.5 block truncate text-[11px] text-[var(--muted)]">
              {citation.location}
            </span>
          )}
        </span>
        {hasDetail && <Chevron open={open} />}
      </button>

      {hasDetail && (
        <div
          id={panelId}
          role="region"
          className={`grid transition-[grid-template-rows] duration-200 ease-out ${
            open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
        >
          <div className="overflow-hidden">
            <div className="space-y-2 border-t border-[var(--line)] px-3 py-2.5 text-[12px] leading-relaxed">
              {citation.location && (
                <p className="text-[var(--muted)]">
                  <span className="font-medium text-[var(--ink-soft)]">
                    Found in:
                  </span>{" "}
                  {citation.location}
                  {citation.clause ? ` · ${citation.clause}` : ""}
                </p>
              )}
              {!citation.location && citation.clause && (
                <p className="text-[var(--muted)]">
                  <span className="font-medium text-[var(--ink-soft)]">
                    Clause:
                  </span>{" "}
                  {citation.clause}
                </p>
              )}
              {citation.quote && (
                <blockquote className="rounded-lg border-l-[3px] border-[var(--accent)] bg-[var(--panel)] px-3 py-2 text-[var(--ink-soft)]">
                  {citation.quote}
                </blockquote>
              )}
              {citation.url && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-[var(--accent)] underline-offset-2 hover:underline"
                >
                  Open official source
                  <span aria-hidden>↗</span>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </li>
  );
}

function CitationAccordion({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const count = citations.length;
  const preview = citations
    .slice(0, 2)
    .map((c) => c.doc)
    .join(" · ");

  return (
    <div className="citation-accordion mt-3 overflow-hidden rounded-2xl border border-[var(--line)] bg-gradient-to-b from-[var(--panel)] to-[var(--surface)] shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-3.5 py-2.5 text-left transition hover:bg-[var(--accent-soft)]/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--ring)]"
      >
        <span
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent-deep)]"
          aria-hidden
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none">
            <path
              d="M7 4h8l4 4v12a1 1 0 01-1 1H7a1 1 0 01-1-1V5a1 1 0 011-1z"
              stroke="currentColor"
              strokeWidth="1.6"
            />
            <path
              d="M15 4v4h4M8 12h8M8 16h6"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className="text-[12.5px] font-semibold tracking-tight text-[var(--ink)]">
              Sources &amp; citations
            </span>
            <span className="rounded-md bg-[var(--accent-soft)] px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-[var(--accent-deep)]">
              {count}
            </span>
          </span>
          {!open && (
            <span className="mt-0.5 block truncate text-[11px] text-[var(--muted)]">
              {preview}
              {count > 2 ? ` +${count - 2} more` : ""}
            </span>
          )}
          {open && (
            <span className="mt-0.5 block text-[11px] text-[var(--muted)]">
              Tap a source for location, quote, and official link
            </span>
          )}
        </span>
        <Chevron open={open} />
      </button>

      <div
        id={panelId}
        role="region"
        className={`grid transition-[grid-template-rows] duration-200 ease-out ${
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="overflow-hidden">
          <ul className="space-y-2 border-t border-[var(--line)] px-2.5 py-2.5">
            {citations.map((citation, index) => (
              <CitationItem
                key={`${citation.doc}-${citation.clause}-${index}`}
                citation={citation}
                index={index}
              />
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[min(720px,92%)] rounded-2xl px-4 py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "text-white shadow-[var(--shadow-soft)]"
            : "border border-[var(--line)] bg-[var(--assistant-bubble)] text-[var(--ink)] shadow-[var(--shadow-soft)] backdrop-blur"
        }`}
        style={
          isUser
            ? { background: "var(--user-bubble)" }
            : undefined
        }
      >
        {!isUser && (
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--accent)]">
            Planning Advisor
          </p>
        )}
        <div className={isUser ? "text-white" : ""}>
          {renderContent(message.content)}
        </div>
        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationAccordion citations={message.citations} />
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  const status = useLoadingStatusMessage(true);

  return (
    <div className="flex justify-start" aria-live="polite" aria-busy="true">
      <div className="max-w-[min(720px,92%)] rounded-2xl border border-[var(--line)] bg-[var(--assistant-bubble)]/95 px-4 py-3 shadow-sm backdrop-blur">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--accent)]">
          Planning Advisor
        </p>
        <div className="flex items-center gap-3 text-sm text-[var(--muted)]">
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--accent)] [animation-delay:-0.2s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--accent)] [animation-delay:-0.1s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--accent)]" />
          </span>
          <span key={status}>{status}</span>
        </div>
      </div>
    </div>
  );
}

export function MessageList() {
  const { activeSession, isSending } = useChat();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession?.messages, isSending]);

  if (!activeSession) return null;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6">
      {activeSession.messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isSending && <TypingIndicator />}
      <div ref={endRef} />
    </div>
  );
}
