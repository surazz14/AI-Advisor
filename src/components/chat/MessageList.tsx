"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/context/ChatContext";
import type { ChatMessage } from "@/types/chat";

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
      </div>
    </div>
  );
}

function TypingIndicator() {
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
          <span>Processing your question…</span>
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
