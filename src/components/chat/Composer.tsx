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
    const text = value;
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
      void submit();
    }
  }

  const showSuggestions =
    !!activeSession &&
    !activeSession.messages.some((m) => m.role === "user") &&
    !value;

  return (
    <div className="border-t border-[var(--line)] bg-[var(--panel)]/90 px-4 py-4 backdrop-blur">
      <div className="mx-auto w-full max-w-3xl">
        {showSuggestions && (
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => void sendMessage(s)}
                className="rounded-full border border-[var(--line)] bg-white/80 px-3 py-1.5 text-left text-xs text-[var(--ink)] transition hover:border-[var(--accent)] hover:text-[var(--accent)]"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={onSubmit}
          className="flex items-end gap-2 rounded-2xl border border-[var(--line)] bg-white p-2 shadow-[0_10px_30px_rgba(15,44,60,0.06)]"
        >
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask about planning rules for your property…"
            className="max-h-40 min-h-[48px] flex-1 resize-none bg-transparent px-3 py-3 text-[15px] text-[var(--ink)] outline-none placeholder:text-[var(--muted)]"
          />
          <button
            type="submit"
            disabled={isSending || !value.trim()}
            className="mb-1 rounded-xl bg-[var(--ink)] px-4 py-2.5 text-sm font-semibold text-white transition enabled:hover:bg-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-[var(--muted)]">
          Answers will cite Local Planning Scheme No. 5 and local policies once
          RAG is connected.
        </p>
      </div>
    </div>
  );
}
