import type { ReactNode } from "react";

/**
 * Lines the backend prepends to every reply with the lot facts. The chat
 * header already shows these as chips, so they are hidden in the message.
 */
const FACT_LINE =
  /^\s*(?:[*_]{1,2})?\s*(?:Using property:|Zoning:|Lot area:|R-Code:|Heritage:|Aboriginal heritage:|Bushfire-prone area:|No property address is set)/i;

/** Stand-alone "Guidance only…" lines (shown once under each answer instead). */
const GUIDANCE_LINE = /^\s*[*_]*\s*Guidance only\b[^\n]*$/i;

export function cleanAnswer(content: string): string {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const kept = lines.filter((line) => !FACT_LINE.test(line) && !GUIDANCE_LINE.test(line));
  return kept
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

type Block =
  | { type: "p"; lines: string[] }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "h"; text: string };

const UL_ITEM = /^\s*(?:[-*•])\s+(.*)$/;
const OL_ITEM = /^\s*\d+[.)]\s+(.*)$/;
const HEADING = /^\s*#{1,6}\s+(.*)$/;

export function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let para: string[] = [];

  const flush = () => {
    if (para.length) blocks.push({ type: "p", lines: para });
    para = [];
  };

  for (const raw of text.split("\n")) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flush();
      continue;
    }
    const h = HEADING.exec(line);
    const ul = UL_ITEM.exec(line);
    const ol = OL_ITEM.exec(line);
    if (h) {
      flush();
      blocks.push({ type: "h", text: h[1] });
    } else if (ul) {
      flush();
      const last = blocks[blocks.length - 1];
      if (last?.type === "ul") last.items.push(ul[1]);
      else blocks.push({ type: "ul", items: [ul[1]] });
    } else if (ol) {
      flush();
      const last = blocks[blocks.length - 1];
      if (last?.type === "ol") last.items.push(ol[1]);
      else blocks.push({ type: "ol", items: [ol[1]] });
    } else {
      const last = blocks[blocks.length - 1];
      // Indented continuation of a list item
      if (!para.length && /^\s{2,}\S/.test(raw) && last && (last.type === "ul" || last.type === "ol")) {
        last.items[last.items.length - 1] += ` ${line.trim()}`;
      } else {
        para.push(line.trim());
      }
    }
  }
  flush();
  return blocks;
}

const INLINE =
  /(\*\*[^*]+\*\*|__[^_]+__|\*[^*\s][^*]*\*|`[^`]+`|\[\d+(?:\s*[,–-]\s*\d+)*\])/g;

export function renderInline(text: string, keyPrefix = "i"): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let n = 0;
  for (const match of text.matchAll(INLINE)) {
    const token = match[0];
    const start = match.index ?? 0;
    if (start > last) out.push(text.slice(last, start));
    const key = `${keyPrefix}-${n++}`;
    if (token.startsWith("**") || token.startsWith("__")) {
      out.push(
        <strong key={key} className="font-semibold">
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith("`")) {
      out.push(
        <code key={key} className="rounded bg-stone-deep px-1 py-0.5 text-[0.92em]">
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("[")) {
      out.push(
        <sup
          key={key}
          className="ml-0.5 font-display text-[0.8em] font-semibold text-accent"
          aria-label={`source ${token.slice(1, -1)}`}
        >
          {token.slice(1, -1)}
        </sup>,
      );
    } else {
      out.push(<em key={key}>{token.slice(1, -1)}</em>);
    }
    last = start + token.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}
