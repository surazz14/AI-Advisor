"use client";

import { FormEvent, KeyboardEvent, useState } from "react";
import { useChat } from "@/context/ChatContext";

const SUGGESTIONS = [
  "Can I build a shed on my rural property?",
  "What fence height is allowed on a street boundary?",
  "Do I need development approval for a new dwelling?",
];

export function Composer() {
  const { sendMessage, isSending, activeSession } = useChat();
  const [value, setValue] = useState("");

  async function submit() {
    if (isSending) return;
    const text = value.trim();
    if (!text) return;
    setValue("");
    await sendMessage(text);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void submit();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) void submit();
    }
  }

  const showSuggestions =
    !!activeSession &&
    !activeSession.messages.some((m) => m.role === "user") &&
    !value &&
    !isSending;

  const canSend = !isSending && Boolean(value.trim());

  return (
    <div className="border-t border-[var(--line)] bg-[var(--panel)]/90 px-4 py-4 backdrop-blur">
      <div className="mx-auto w-full max-w-3xl">
        {isSending && (
          <p
            className="mb-3 text-center text-xs font-medium text-[var(--accent-deep)]"
            aria-live="polite"
          >
            Please wait — your question is being processed…
          </p>
        )}

        {showSuggestions && (
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                disabled={isSending}
                onClick={() => {
                  if (!isSending) void sendMessage(s);
                }}
                className="rounded-full border border-[var(--line)] bg-[var(--accent-soft)] px-3 py-1.5 text-left text-xs text-[var(--ink-soft)] transition hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={onSubmit}
          className={`flex items-end gap-2 rounded-2xl border bg-white/95 p-2 shadow-[var(--shadow-lift)] ${
            isSending
              ? "border-[var(--accent)]/45 opacity-90"
              : "border-[var(--line)]"
          }`}
        >
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={isSending}
            aria-busy={isSending}
            placeholder={
              isSending
                ? "Waiting for the planning advisor…"
                : "Ask about planning rules for your property…"
            }
            className="max-h-40 min-h-[48px] flex-1 resize-none bg-transparent px-3 py-3 text-[15px] text-[var(--ink)] outline-none placeholder:text-[var(--muted)] disabled:cursor-not-allowed disabled:text-[var(--muted)]"
          />
          <button
            type="submit"
            disabled={!canSend}
            className="mb-1 inline-flex min-w-[88px] items-center justify-center rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_8px_18px_rgba(31,154,92,0.28)] transition enabled:hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            {isSending ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Wait
              </span>
            ) : (
              "Send"
            )}
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-[var(--muted)]">
          {isSending
            ? "Input is locked until the current answer finishes."
            : "Answers will cite Local Planning Scheme No. 5 and local policies once RAG is connected."}
        </p>
      </div>
    </div>
  );
}
