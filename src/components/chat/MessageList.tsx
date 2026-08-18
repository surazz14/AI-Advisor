"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/context/ChatContext";
import type { ChatMessage } from "@/types/chat";

function renderContent(content: string) {
  // very small markdown-ish: **bold** and newlines
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
        className={`max-w-[min(720px,92%)] rounded-2xl px-4 py-3 text-[15px] leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-[var(--accent)] text-white shadow-sm"
            : "border border-[var(--line)] bg-white/90 text-[var(--ink)] shadow-sm backdrop-blur"
        }`}
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
      {isSending && (
        <div className="flex justify-start">
          <div className="rounded-2xl border border-[var(--line)] bg-white/90 px-4 py-3 text-sm text-[var(--muted)]">
            Checking planning context…
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
