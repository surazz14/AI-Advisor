"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useChat } from "@/context/ChatContext";
import { LOADING_STATUS_MESSAGES, useLoadingStep } from "@/hooks/useLoadingStatusMessage";
import { cleanAnswer, parseBlocks, renderInline } from "@/lib/renderAnswer";
import type { ChatMessage, Citation } from "@/types/chat";
import { AdvisorAvatar, Icon, Spinner } from "@/components/brand/Brand";

export const STARTER_QUESTIONS = [
  "Can I put up a shed without approval?",
  "How high can my front fence be?",
  "Can I add a granny flat?",
  "What size water tank is allowed?",
] as const;

/* ———————————————————————— Answer body ———————————————————————— */

function AnswerBody({ text }: { text: string }) {
  const blocks = parseBlocks(text);
  const first = blocks[0];
  const leadIsShort =
    blocks.length > 1 &&
    first?.type === "p" &&
    first.lines.length === 1 &&
    first.lines[0].length <= 220;

  return (
    <div className="flex flex-col gap-3.5 text-[16px] leading-[1.7] sm:text-[17px]">
      {blocks.map((block, bi) => {
        const key = `b${bi}`;
        if (block.type === "h") {
          return (
            <h3 key={key} className="pt-1 text-[17px] font-semibold leading-snug">
              {renderInline(block.text, key)}
            </h3>
          );
        }
        if (block.type === "ul" || block.type === "ol") {
          const List = block.type;
          return (
            <List
              key={key}
              className={`flex flex-col gap-1.5 pl-6 ${block.type === "ul" ? "list-disc" : "list-decimal"} marker:text-muted`}
            >
              {block.items.map((item, ii) => (
                <li key={`${key}-${ii}`} className="pl-1">
                  {renderInline(item, `${key}-${ii}`)}
                </li>
              ))}
            </List>
          );
        }
        if (bi === 0 && leadIsShort) {
          return (
            <p
              key={key}
              className="font-display text-[22px] font-medium leading-[1.32] sm:text-[26px]"
            >
              {renderInline(block.lines[0], key)}
            </p>
          );
        }
        return (
          <p key={key}>
            {block.lines.map((line, li) => (
              <span key={`${key}-${li}`}>
                {li > 0 && <br />}
                {renderInline(line, `${key}-${li}`)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}

/* ———————————————————————— Sources ———————————————————————— */

function SourceItem({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const hasDetail = Boolean(citation.quote || citation.location || citation.url);
  const title = citation.topic ? `${citation.doc} — ${citation.topic}` : citation.doc;

  return (
    <li className="overflow-hidden rounded-xl border border-line bg-paper">
      <div className="flex items-start gap-3 px-3.5 py-3">
        <span className="w-4 flex-none pt-px text-center font-display text-lg leading-none text-accent">
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <button
            type="button"
            aria-expanded={hasDetail ? open : undefined}
            aria-controls={hasDetail ? panelId : undefined}
            onClick={() => hasDetail && setOpen((v) => !v)}
            className={`flex w-full items-start justify-between gap-2 text-left ${hasDetail ? "" : "cursor-default"}`}
          >
            <span className="min-w-0">
              <span className="block text-[15px] font-semibold leading-snug">{title}</span>
              {citation.location && !open && (
                <span className="mt-0.5 block truncate text-[13px] text-muted">{citation.location}</span>
              )}
            </span>
            {hasDetail && (
              <Icon
                name="chevron"
                className={`mt-0.5 h-[18px] w-[18px] flex-none text-muted transition-transform ${open ? "rotate-180" : ""}`}
              />
            )}
          </button>
          {hasDetail && open && (
            <div id={panelId} className="mt-2.5 flex flex-col gap-2.5 text-[14px] leading-relaxed">
              {citation.location && (
                <p className="text-muted">
                  <span className="font-semibold text-ink">Found in:</span> {citation.location}
                </p>
              )}
              {citation.quote && (
                <blockquote className="rounded-lg bg-stone px-3 py-2.5 text-[#3f382f]">
                  “{citation.quote}”
                </blockquote>
              )}
              {citation.url && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-10 items-center gap-1.5 self-start font-semibold text-accent underline-offset-2 hover:underline"
                >
                  Open the official document
                  <Icon name="external" className="h-4 w-4" />
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function Sources({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const preview = Array.from(new Set(citations.map((c) => c.doc))).slice(0, 2).join(" · ");

  return (
    <div className="border-t border-line pt-3">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="flex min-h-11 w-full items-center justify-between gap-3 text-left"
      >
        <span className="min-w-0">
          <span className="block text-[15px] font-semibold">Sources ({citations.length})</span>
          {!open && <span className="block truncate text-[13px] text-muted">{preview}</span>}
        </span>
        <Icon
          name="chevron"
          className={`h-5 w-5 flex-none text-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <ol id={panelId} className="mt-2 flex flex-col gap-2">
          {citations.map((citation, index) => (
            <SourceItem
              key={`${citation.doc}-${citation.clause ?? ""}-${index}`}
              citation={citation}
              index={index}
            />
          ))}
        </ol>
      )}
    </div>
  );
}

/* ———————————————————————— Messages ———————————————————————— */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 1800);
    return () => clearTimeout(t);
  }, [copied]);

  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
        } catch {
          // clipboard blocked — nothing to do
        }
      }}
      aria-label={copied ? "Copied" : "Copy answer"}
      className="inline-flex h-10 min-w-10 items-center justify-center gap-1.5 rounded-xl border border-line px-2.5 text-sm text-ink transition hover:bg-paper"
    >
      <Icon name={copied ? "check" : "copy"} className="h-[18px] w-[18px]" />
      {copied && <span>Copied</span>}
    </button>
  );
}

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="rise-in flex justify-end">
      <div className="max-w-[86%] whitespace-pre-wrap rounded-[20px] rounded-br-[4px] bg-sand px-4 py-3 text-[16px] leading-relaxed sm:max-w-[78%] sm:px-[18px] sm:py-3.5 sm:text-[17px]">
        {message.content}
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const text = cleanAnswer(message.content);
  return (
    <article className="rise-in flex flex-col gap-3.5" aria-label="Advisor answer">
      <div className="flex items-center gap-2.5">
        <AdvisorAvatar />
        <span className="text-sm font-semibold">Advisor</span>
      </div>
      <AnswerBody text={text || message.content} />
      {message.citations && message.citations.length > 0 && (
        <Sources citations={message.citations} />
      )}
      <div className="flex flex-wrap items-center gap-2 text-sm text-muted">
        <CopyButton text={text || message.content} />
        <span className="ml-1">Guidance only — not a formal planning decision.</span>
      </div>
    </article>
  );
}

function ErrorMessage({ message, onRetry }: { message: ChatMessage; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="rise-in flex gap-3 rounded-2xl bg-danger-soft p-4 text-[15px] leading-relaxed text-danger-ink"
    >
      <Icon name="alert" className="mt-0.5 h-[22px] w-[22px] flex-none text-danger" />
      <div className="flex flex-1 flex-col items-start gap-2.5">
        <p>{message.content}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="min-h-10 rounded-lg border border-danger px-3.5 text-sm font-semibold"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

function Welcome({ showStarters }: { showStarters: boolean }) {
  const { sendMessage, isSending } = useChat();
  return (
    <section className="rise-in flex flex-col gap-3.5" aria-label="Get started">
      <div className="flex items-start gap-3">
        <AdvisorAvatar />
        <p className="pt-1 text-[16px] leading-relaxed text-muted">
          I’ve found your lot. Ask me anything about building or changing things on it.
        </p>
      </div>
      {showStarters && (
        <>
          <p className="mt-2 font-display text-[24px] font-medium leading-tight sm:text-[28px]">
            What are you thinking of building?
          </p>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {STARTER_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                disabled={isSending}
                onClick={() => void sendMessage(q)}
                className="flex min-h-14 items-center justify-between gap-3 rounded-2xl border border-line bg-paper px-4 text-left text-[16px] font-medium transition hover:border-accent disabled:opacity-60"
              >
                {q}
                <Icon name="arrow" className="h-[18px] w-[18px] flex-none text-accent" />
              </button>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function Thinking() {
  const step = useLoadingStep();
  const steps = LOADING_STATUS_MESSAGES.slice(0, 4);
  const late = step >= steps.length ? LOADING_STATUS_MESSAGES[step] : null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="rise-in flex flex-col gap-3 rounded-2xl border border-line bg-paper p-4 sm:max-w-md"
    >
      <div className="flex items-center gap-2.5">
        <AdvisorAvatar size="h-7 w-7" />
        <span className="text-[15px] font-semibold">Working on it…</span>
      </div>
      <ul className="flex flex-col gap-2.5 text-[15px]">
        {steps.map((label, i) => {
          const done = i < step;
          const current = i === Math.min(step, steps.length - 1) && !done;
          return (
            <li key={label} className={`flex items-center gap-2.5 ${done ? "" : "text-muted"}`}>
              {done ? (
                <span className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-full bg-accent text-white">
                  <Icon name="check" className="h-3 w-3" />
                </span>
              ) : current ? (
                <Spinner className="h-[18px] w-[18px] text-accent" />
              ) : (
                <span className="h-[18px] w-[18px] rounded-full border-2 border-line" aria-hidden />
              )}
              {label.replace(/…$/, "")}
            </li>
          );
        })}
      </ul>
      {late && <p className="text-sm text-muted">{late}</p>}
    </div>
  );
}

export function MessageList() {
  const { activeSession, isSending, sendMessage } = useChat();
  const endRef = useRef<HTMLDivElement>(null);
  const count = activeSession?.messages.length ?? 0;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [count, isSending]);

  if (!activeSession) return null;
  const messages = activeSession.messages;
  const hasUser = messages.some((m) => m.role === "user");

  return (
    <div className="mx-auto flex w-full max-w-[820px] flex-col gap-7 px-4 py-6 sm:px-8 sm:py-8">
      {messages.length === 0 && <Welcome showStarters={!isSending} />}
      {messages.map((message, index) => {
        if (message.role === "user") return <UserMessage key={message.id} message={message} />;
        if (message.kind === "welcome") {
          return <Welcome key={message.id} showStarters={!hasUser && !isSending} />;
        }
        if (message.kind === "error") {
          const isLast = index === messages.length - 1;
          const previousUser = [...messages.slice(0, index)].reverse().find((m) => m.role === "user");
          return (
            <ErrorMessage
              key={message.id}
              message={message}
              onRetry={
                isLast && previousUser && !isSending
                  ? () => void sendMessage(previousUser.content)
                  : undefined
              }
            />
          );
        }
        return <AssistantMessage key={message.id} message={message} />;
      })}
      {isSending && <Thinking />}
      <div ref={endRef} />
    </div>
  );
}
