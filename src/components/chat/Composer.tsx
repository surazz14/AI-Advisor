"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useChat } from "@/context/ChatContext";
import { Icon, Spinner } from "@/components/brand/Brand";

const MAX_HEIGHT_PX = 180;

export function Composer() {
  const { sendMessage, isSending } = useChat();
  // A question passed from the home page as /chat?ask=…
  const ask = useSearchParams().get("ask")?.slice(0, 500) ?? "";
  const [value, setValue] = useState(ask);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Drop ?ask= from the URL once it has been used to prefill the box.
  useEffect(() => {
    if (ask) window.history.replaceState(null, "", window.location.pathname);
  }, [ask]);

  function resize(el: HTMLTextAreaElement | null) {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`;
  }

  async function submit() {
    const text = value.trim();
    if (isSending || !text) return;
    setValue("");
    requestAnimationFrame(() => resize(inputRef.current));
    await sendMessage(text);
    inputRef.current?.focus();
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void submit();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void submit();
    }
  }

  const canSend = !isSending && Boolean(value.trim());

  return (
    <div className="border-t border-line bg-stone px-3 pb-3 pt-3 sm:px-8 sm:pb-4">
      <div className="mx-auto w-full max-w-[820px]">
        <form
          onSubmit={onSubmit}
          className={`flex items-end gap-2.5 rounded-[26px] border bg-paper py-1.5 pl-5 pr-1.5 transition focus-within:border-accent ${
            isSending ? "border-line opacity-90" : "border-line"
          }`}
        >
          <label htmlFor="chat-input" className="sr-only">
            Ask about your property
          </label>
          <textarea
            id="chat-input"
            ref={inputRef}
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              resize(e.target);
            }}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={isSending}
            aria-busy={isSending}
            maxLength={2000}
            placeholder={isSending ? "Wait for the answer…" : "Ask about your property…"}
            className="max-h-[180px] min-h-[48px] flex-1 resize-none bg-transparent py-3 text-[16px] leading-6 text-ink outline-none placeholder:text-muted disabled:cursor-not-allowed sm:text-[17px]"
            style={{ outline: "none" }}
          />
          <button
            type="submit"
            disabled={!canSend}
            aria-label={isSending ? "Waiting for the answer" : "Send"}
            className="inline-flex h-12 w-12 flex-none items-center justify-center rounded-full bg-accent text-white transition enabled:hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-line-strong"
          >
            {isSending ? <Spinner className="h-5 w-5" /> : <Icon name="arrow" className="h-5 w-5" />}
          </button>
        </form>
        <p className="mt-2 text-center text-[13px] text-muted">
          <span className="hidden sm:inline">Enter to send · Shift + Enter for a new line · </span>
          Guidance only — confirm with the Shire before you build.
        </p>
      </div>
    </div>
  );
}
