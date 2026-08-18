"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { ChatMessage, ChatSession, PropertyFacts } from "@/types/chat";

const STORAGE_KEY = "plantagenet-planning-advisor-v1";

type ChatContextValue = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  activeSession: ChatSession | null;
  isSidebarOpen: boolean;
  isSending: boolean;
  createSession: () => void;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => void;
  sendMessage: (content: string) => Promise<void>;
  updatePropertyFacts: (facts: Partial<PropertyFacts>) => void;
  setSidebarOpen: (open: boolean) => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function makeWelcomeMessage(): ChatMessage {
  return {
    id: uid(),
    role: "assistant",
    content:
      "Hello — I’m the Plantagenet Planning Advisor.\n\nAsk about sheds, fences, dwellings, setbacks, or bushfire-related planning questions for land in the Shire of Plantagenet.\n\nTip: share your property address first so answers can use zoning and bushfire context.\n\nGuidance only — not a formal planning decision.",
    createdAt: new Date().toISOString(),
  };
}

function makeSession(): ChatSession {
  const now = new Date().toISOString();
  return {
    id: uid(),
    title: "New planning chat",
    messages: [makeWelcomeMessage()],
    propertyFacts: {},
    updatedAt: now,
  };
}

function titleFromPrompt(prompt: string) {
  const clean = prompt.trim().replace(/\s+/g, " ");
  return clean.length > 42 ? `${clean.slice(0, 42)}…` : clean || "New planning chat";
}

/** Temporary local reply until FastAPI + RAG is connected */
function mockAdvisorReply(prompt: string, facts: PropertyFacts): string {
  const lower = prompt.toLowerCase();
  const locationLine = facts.address
    ? `Using property context: **${facts.address}**${facts.zone ? ` · Zone: **${facts.zone}**` : ""}${
        facts.bushfireProne != null
          ? ` · Bushfire prone: **${facts.bushfireProne ? "Yes" : "No"}**`
          : ""
      }`
    : "No address is set yet — add one in the property panel for site-specific guidance.";

  if (lower.includes("fence")) {
    return `${locationLine}\n\nFor fencing questions I will later retrieve the relevant **Local Planning Scheme No. 5** and **Local Planning Policy** clauses (RAG).\n\nFor now: tell me the proposed height, materials, and whether it is a street or side boundary.\n\n*Demo reply — backend RAG not connected yet.*`;
  }

  if (lower.includes("shed") || lower.includes("outbuilding")) {
    return `${locationLine}\n\nShed / outbuilding advice will be grounded in retrieved LPS No. 5 and local policy text, plus your lot facts.\n\nUseful details to include: size (m²), height, and roughly where on the lot it will sit.\n\n*Demo reply — backend RAG not connected yet.*`;
  }

  if (lower.includes("dwelling") || lower.includes("house") || lower.includes("build")) {
    return `${locationLine}\n\nDwelling questions usually need zoning, bushfire status, and setback rules from the scheme/policies.\n\nOnce RAG is connected, answers will cite the exact clauses used.\n\n*Demo reply — backend RAG not connected yet.*`;
  }

  return `${locationLine}\n\nI received: “${prompt.trim()}”\n\nSoon this chatbot will:\n1. Keep this conversation in context\n2. Resolve your address to lot / zone / bushfire facts\n3. Retrieve matching policy rows (RAG)\n4. Answer with citations\n\n*Demo reply — backend RAG not connected yet.*`;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const sessionsRef = useRef(sessions);
  sessionsRef.current = sessions;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          sessions: ChatSession[];
          activeSessionId: string | null;
        };
        if (parsed.sessions?.length) {
          setSessions(parsed.sessions);
          setActiveSessionId(parsed.activeSessionId ?? parsed.sessions[0].id);
          setHydrated(true);
          return;
        }
      }
    } catch {
      // ignore corrupt storage
    }
    const first = makeSession();
    setSessions([first]);
    setActiveSessionId(first.id);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ sessions, activeSessionId }),
    );
  }, [sessions, activeSessionId, hydrated]);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  );

  const createSession = useCallback(() => {
    const session = makeSession();
    setSessions((prev) => [session, ...prev]);
    setActiveSessionId(session.id);
  }, []);

  const selectSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        if (!next.length) {
          const fresh = makeSession();
          setActiveSessionId(fresh.id);
          return [fresh];
        }
        if (activeSessionId === id) {
          setActiveSessionId(next[0].id);
        }
        return next;
      });
    },
    [activeSessionId],
  );

  const updatePropertyFacts = useCallback(
    (facts: Partial<PropertyFacts>) => {
      if (!activeSessionId) return;
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId
            ? {
                ...s,
                propertyFacts: { ...s.propertyFacts, ...facts },
                updatedAt: new Date().toISOString(),
              }
            : s,
        ),
      );
    },
    [activeSessionId],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || !activeSessionId || isSending) return;

      const userMessage: ChatMessage = {
        id: uid(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
      };

      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== activeSessionId) return s;
          const isFirstUser = !s.messages.some((m) => m.role === "user");
          return {
            ...s,
            title: isFirstUser ? titleFromPrompt(trimmed) : s.title,
            messages: [...s.messages, userMessage],
            updatedAt: new Date().toISOString(),
          };
        }),
      );

      setIsSending(true);
      try {
        // Simulate network latency for chatbot feel
        await new Promise((r) => setTimeout(r, 650));
        const facts =
          sessionsRef.current.find((s) => s.id === activeSessionId)
            ?.propertyFacts ?? {};

        const assistantMessage: ChatMessage = {
          id: uid(),
          role: "assistant",
          content: mockAdvisorReply(trimmed, facts),
          createdAt: new Date().toISOString(),
        };
        setSessions((prev) =>
          prev.map((s) =>
            s.id === activeSessionId
              ? {
                  ...s,
                  messages: [...s.messages, assistantMessage],
                  updatedAt: new Date().toISOString(),
                }
              : s,
          ),
        );
      } finally {
        setIsSending(false);
      }
    },
    [activeSessionId, isSending],
  );

  const value: ChatContextValue = {
    sessions,
    activeSessionId,
    activeSession,
    isSidebarOpen,
    isSending,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
    updatePropertyFacts,
    setSidebarOpen,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error("useChat must be used within ChatProvider");
  }
  return ctx;
}
