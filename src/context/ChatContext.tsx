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
import { useSocket } from "@/context/SocketContext";
import {
  displayLocation,
  type ChatMessage,
  type ChatSession,
  type PropertyFacts,
} from "@/types/chat";

const STORAGE_KEY = "plantagenet-planning-advisor-v3";
const SOCKET_REPLY_TIMEOUT_MS = 20000;

type LocationInput = {
  address: string;
  lat?: number;
  lng?: number;
};

type ChatContextValue = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  activeSession: ChatSession | null;
  isSidebarOpen: boolean;
  isSending: boolean;
  createSession: () => void;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => void;
  startChatWithAddress: (input: LocationInput) => void;
  resetLocation: () => void;
  sendMessage: (content: string) => Promise<void>;
  setSidebarOpen: (open: boolean) => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function makeWelcomeMessage(locationLabel: string): ChatMessage {
  return {
    id: uid(),
    role: "assistant",
    content: `Thanks — I’ve saved your property as **${locationLabel}**.\n\nAsk about sheds, fences, dwellings, setbacks, or bushfire-related planning questions for this site in the Shire of Plantagenet.\n\nGuidance only — not a formal planning decision.`,
    createdAt: new Date().toISOString(),
  };
}

function makeSession(): ChatSession {
  return {
    id: uid(),
    title: "New planning chat",
    messages: [],
    propertyFacts: {},
    locationReady: false,
    updatedAt: new Date().toISOString(),
  };
}

function titleFromPrompt(prompt: string) {
  const clean = prompt.trim().replace(/\s+/g, " ");
  return clean.length > 42 ? `${clean.slice(0, 42)}…` : clean || "New planning chat";
}

function normalizeSessions(sessions: ChatSession[]): ChatSession[] {
  return sessions.map((s) => ({
    ...s,
    locationReady:
      s.locationReady ?? Boolean(s.propertyFacts?.address?.trim()),
    propertyFacts: {
      address: s.propertyFacts?.address,
      lat: s.propertyFacts?.lat,
      lng: s.propertyFacts?.lng,
    },
  }));
}

/** Temporary local reply until FastAPI socket backend is available */
function mockAdvisorReply(prompt: string, facts: PropertyFacts): string {
  const lower = prompt.toLowerCase();
  const location = displayLocation(facts);
  const locationLine = location
    ? `Using property: **${location}**`
    : "No property address is set.";

  if (lower.includes("fence")) {
    return `${locationLine}\n\nFor fencing questions I will later retrieve the relevant **Local Planning Scheme No. 5** and **Local Planning Policy** clauses (RAG).\n\nFor now: tell me the proposed height, materials, and whether it is a street or side boundary.\n\n*Demo reply — chat socket backend not connected.*`;
  }

  if (lower.includes("shed") || lower.includes("outbuilding")) {
    return `${locationLine}\n\nShed / outbuilding advice will be grounded in retrieved LPS No. 5 and local policy text.\n\nUseful details to include: size (m²), height, and roughly where on the lot it will sit.\n\n*Demo reply — chat socket backend not connected.*`;
  }

  if (lower.includes("dwelling") || lower.includes("house") || lower.includes("build")) {
    return `${locationLine}\n\nDwelling questions usually need zoning, bushfire status, and setback rules from the scheme/policies.\n\nOnce RAG is connected, answers will cite the exact clauses used.\n\n*Demo reply — chat socket backend not connected.*`;
  }

  return `${locationLine}\n\nI received: “${prompt.trim()}”\n\nConnect the FastAPI WebSocket at \`NEXT_PUBLIC_WS_URL\` to stream live answers.\n\n*Demo reply — chat socket backend not connected.*`;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { isConnected, send, subscribe } = useSocket();
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
          const sessionsNormalized = normalizeSessions(parsed.sessions);
          setSessions(sessionsNormalized);
          setActiveSessionId(
            parsed.activeSessionId ?? sessionsNormalized[0].id,
          );
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

  // Introduce session to backend when socket connects / address becomes ready
  useEffect(() => {
    if (!isConnected || !activeSessionId) return;
    const session = sessionsRef.current.find((s) => s.id === activeSessionId);
    if (!session?.locationReady || !session.propertyFacts.address) return;
    try {
      send({
        type: "session.hello",
        sessionId: session.id,
        address: session.propertyFacts.address,
        lat: session.propertyFacts.lat,
        lng: session.propertyFacts.lng,
      });
    } catch {
      // backend may not be ready yet
    }
  }, [isConnected, activeSessionId, send]);

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

  const startChatWithAddress = useCallback(
    (input: LocationInput) => {
      if (!activeSessionId) return;
      const address = input.address.trim();
      if (!address) return;

      const facts: PropertyFacts = {
        address,
        lat: input.lat,
        lng: input.lng,
      };
      const label = displayLocation(facts);

      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId
            ? {
                ...s,
                title: label.slice(0, 42) || "Planning chat",
                propertyFacts: facts,
                locationReady: true,
                messages: [makeWelcomeMessage(label)],
                updatedAt: new Date().toISOString(),
              }
            : s,
        ),
      );

      if (isConnected) {
        try {
          send({
            type: "session.hello",
            sessionId: activeSessionId,
            address,
            lat: input.lat,
            lng: input.lng,
          });
        } catch {
          // ignore until backend is up
        }
      }
    },
    [activeSessionId, isConnected, send],
  );

  const resetLocation = useCallback(() => {
    if (!activeSessionId) return;
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId
          ? {
              ...s,
              title: "New planning chat",
              propertyFacts: {},
              locationReady: false,
              messages: [],
              updatedAt: new Date().toISOString(),
            }
          : s,
      ),
    );
  }, [activeSessionId]);

  const appendAssistant = useCallback(
    (sessionId: string, content: string) => {
      const assistantMessage: ChatMessage = {
        id: uid(),
        role: "assistant",
        content,
        createdAt: new Date().toISOString(),
      };
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                messages: [...s.messages, assistantMessage],
                updatedAt: new Date().toISOString(),
              }
            : s,
        ),
      );
    },
    [],
  );

  const waitForSocketReply = useCallback(
    (sessionId: string) =>
      new Promise<string>((resolve, reject) => {
        const timer = setTimeout(() => {
          unsub();
          reject(new Error("Timed out waiting for chat server reply"));
        }, SOCKET_REPLY_TIMEOUT_MS);

        const unsub = subscribe((event) => {
          if (event.type === "chat.assistant" && event.sessionId === sessionId) {
            clearTimeout(timer);
            unsub();
            resolve(event.content);
          }
          if (
            event.type === "chat.error" &&
            (!event.sessionId || event.sessionId === sessionId)
          ) {
            clearTimeout(timer);
            unsub();
            reject(new Error(event.message));
          }
        });
      }),
    [subscribe],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      const current = sessionsRef.current.find((s) => s.id === activeSessionId);
      if (!trimmed || !activeSessionId || isSending || !current?.locationReady) {
        return;
      }

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
        if (isConnected) {
          send({
            type: "chat.send",
            sessionId: activeSessionId,
            content: trimmed,
            address: current.propertyFacts.address,
            lat: current.propertyFacts.lat,
            lng: current.propertyFacts.lng,
          });
          const reply = await waitForSocketReply(activeSessionId);
          appendAssistant(activeSessionId, reply);
        } else {
          await new Promise((r) => setTimeout(r, 650));
          appendAssistant(
            activeSessionId,
            mockAdvisorReply(trimmed, current.propertyFacts),
          );
        }
      } catch (error) {
        appendAssistant(
          activeSessionId,
          `I couldn’t reach the chat server.\n\n${
            error instanceof Error ? error.message : "Unknown socket error"
          }\n\nShowing a local demo reply instead:\n\n${mockAdvisorReply(
            trimmed,
            current.propertyFacts,
          )}`,
        );
      } finally {
        setIsSending(false);
      }
    },
    [
      activeSessionId,
      appendAssistant,
      isConnected,
      isSending,
      send,
      waitForSocketReply,
    ],
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
    startChatWithAddress,
    resetLocation,
    sendMessage,
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
