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
import { getChatSocket } from "@/lib/chatSocket";
import type { ServerSocketEvent } from "@/types/socket";
import {
  shortAddress,
  type ChatMessage,
  type ChatSession,
  type PropertyFacts,
} from "@/types/chat";

const STORAGE_KEY = "plantagenet-planning-advisor-v3";
const SOCKET_REPLY_TIMEOUT_MS = 120000;
const CONNECT_TIMEOUT_MS = 10000;

type LocationInput = {
  address: string;
  lat?: number;
  lng?: number;
};

type AssistantEvent = Extract<ServerSocketEvent, { type: "chat.assistant" }>;

type ChatContextValue = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  activeSession: ChatSession | null;
  isSidebarOpen: boolean;
  isSending: boolean;
  /** True once saved chats have been read from this browser */
  hydrated: boolean;
  createSession: () => void;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => void;
  /** Confirm an address for the active (empty) chat */
  startChatWithAddress: (input: LocationInput) => Promise<void>;
  /** Confirm an address in a fresh chat (reuses the active chat if it is still empty) */
  startNewChatWithAddress: (input: LocationInput) => Promise<void>;
  resetLocation: () => void;
  sendMessage: (content: string) => Promise<void>;
  setSidebarOpen: (open: boolean) => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
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
  return sessions
    .filter((s) => s && typeof s.id === "string")
    .map((s) => ({
      ...s,
      messages: Array.isArray(s.messages) ? s.messages : [],
      locationReady:
        s.locationReady ?? Boolean(s.propertyFacts?.address?.trim()),
      propertyFacts: { ...(s.propertyFacts ?? {}) },
    }));
}

/** Live lot facts carried on every advisor reply. */
function factsFromEvent(event: AssistantEvent): Partial<PropertyFacts> {
  const facts: Partial<PropertyFacts> = {};
  if (event.zone?.zone) facts.zone = event.zone.zone;
  if (typeof event.lotAreaM2 === "number") facts.lotAreaM2 = event.lotAreaM2;
  if (event.rCode) facts.rCode = event.rCode;
  if (Array.isArray(event.heritage)) facts.heritage = event.heritage;
  if (typeof event.bushfireProne === "boolean") {
    facts.bushfireProne = event.bushfireProne;
  }
  return facts;
}

function offlineMessage() {
  return "The advisor service isn’t reachable right now. Please try again in a moment.";
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { isConnected, send, subscribe, connect } = useSocket();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const sessionsRef = useRef(sessions);

  useEffect(() => {
    sessionsRef.current = sessions;
  }, [sessions]);

  // Restore saved chats from this browser (client only).
  useEffect(() => {
    let restored: { sessions: ChatSession[]; active: string | null } | null = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          sessions?: ChatSession[];
          activeSessionId?: string | null;
        };
        if (parsed.sessions?.length) {
          const normalized = normalizeSessions(parsed.sessions);
          if (normalized.length) {
            const active =
              parsed.activeSessionId &&
              normalized.some((s) => s.id === parsed.activeSessionId)
                ? parsed.activeSessionId
                : normalized[0].id;
            restored = { sessions: normalized, active };
          }
        }
      }
    } catch {
      // ignore corrupt or blocked storage
    }
    const next = restored ?? { sessions: [makeSession()], active: null };
    // Reading browser storage has to happen after mount to avoid a hydration
    // mismatch, so this one-off sync setState in an effect is intentional.
    /* eslint-disable react-hooks/set-state-in-effect */
    setSessions(next.sessions);
    setActiveSessionId(next.active ?? next.sessions[0].id);
    setHydrated(true);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ sessions, activeSessionId }),
      );
    } catch {
      // storage full or blocked — chats still work for this visit
    }
  }, [sessions, activeSessionId, hydrated]);

  // Re-introduce the active chat to the backend after (re)connecting.
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
      const remaining = sessionsRef.current.filter((s) => s.id !== id);
      if (remaining.length === 0) {
        const fresh = makeSession();
        setSessions([fresh]);
        setActiveSessionId(fresh.id);
        return;
      }
      setSessions(remaining);
      if (activeSessionId === id) {
        setActiveSessionId(remaining[0].id);
      }
    },
    [activeSessionId],
  );

  const updateSession = useCallback(
    (sessionId: string, update: (s: ChatSession) => ChatSession) => {
      setSessions((prev) => prev.map((s) => (s.id === sessionId ? update(s) : s)));
    },
    [],
  );

  const appendAssistant = useCallback(
    (
      sessionId: string,
      content: string,
      extras: {
        citations?: ChatMessage["citations"];
        kind?: ChatMessage["kind"];
        facts?: Partial<PropertyFacts>;
      } = {},
    ) => {
      const assistantMessage: ChatMessage = {
        id: uid(),
        role: "assistant",
        content,
        createdAt: new Date().toISOString(),
        ...(extras.citations && extras.citations.length > 0
          ? { citations: extras.citations }
          : {}),
        ...(extras.kind ? { kind: extras.kind } : {}),
      };
      updateSession(sessionId, (s) => ({
        ...s,
        messages: [...s.messages, assistantMessage],
        propertyFacts: { ...s.propertyFacts, ...(extras.facts ?? {}) },
        updatedAt: new Date().toISOString(),
      }));
    },
    [updateSession],
  );

  const waitForSocketReply = useCallback(
    (sessionId: string) =>
      new Promise<AssistantEvent>((resolve, reject) => {
        const timer = setTimeout(() => {
          unsub();
          reject(
            new Error(
              "The advisor took too long to reply. Please try asking again.",
            ),
          );
        }, SOCKET_REPLY_TIMEOUT_MS);

        const unsub = subscribe((event) => {
          if (event.type === "chat.assistant" && event.sessionId === sessionId) {
            clearTimeout(timer);
            unsub();
            resolve(event);
          }
          if (event.type === "chat.error" && event.sessionId === sessionId) {
            clearTimeout(timer);
            unsub();
            reject(new Error(event.message));
          }
          if (event.type === "chat.error" && !event.sessionId) {
            // Server-wide failure (e.g. invalid message) — stop waiting.
            clearTimeout(timer);
            unsub();
            reject(new Error(event.message));
          }
        });
      }),
    [subscribe],
  );

  const ensureConnected = useCallback(async () => {
    if (isConnected) return true;
    return getChatSocket().waitUntilConnected(CONNECT_TIMEOUT_MS);
  }, [isConnected]);

  /** Send session.hello for an address and wait for the welcome reply. */
  const confirmAddress = useCallback(
    async (sessionId: string, input: LocationInput) => {
      const address = input.address.trim();
      if (!address) throw new Error("Enter a property address to continue.");
      if (input.lat == null || input.lng == null) {
        throw new Error(
          "Please pick an address from the suggestions so we can confirm it is in the Shire of Plantagenet.",
        );
      }

      if (!(await ensureConnected())) {
        connect();
        throw new Error(offlineMessage());
      }

      setIsSending(true);
      try {
        const welcomePromise = waitForSocketReply(sessionId);
        send({
          type: "session.hello",
          sessionId,
          address,
          lat: input.lat,
          lng: input.lng,
        });
        const welcome = await welcomePromise;
        updateSession(sessionId, (s) => ({
          ...s,
          title: shortAddress(address).slice(0, 42) || "Planning chat",
          propertyFacts: {
            address,
            lat: input.lat,
            lng: input.lng,
            ...factsFromEvent(welcome),
          },
          locationReady: true,
          messages: [
            {
              id: uid(),
              role: "assistant",
              content: welcome.content,
              createdAt: new Date().toISOString(),
              kind: "welcome",
            },
          ],
          updatedAt: new Date().toISOString(),
        }));
      } catch (error) {
        updateSession(sessionId, (s) => ({
          ...s,
          propertyFacts: {},
          locationReady: false,
          messages: [],
          updatedAt: new Date().toISOString(),
        }));
        throw error instanceof Error
          ? error
          : new Error("We couldn’t check this address. Please try again.");
      } finally {
        setIsSending(false);
      }
    },
    [connect, ensureConnected, send, updateSession, waitForSocketReply],
  );

  const startChatWithAddress = useCallback(
    async (input: LocationInput) => {
      if (!activeSessionId || isSending) return;
      await confirmAddress(activeSessionId, input);
    },
    [activeSessionId, confirmAddress, isSending],
  );

  const startNewChatWithAddress = useCallback(
    async (input: LocationInput) => {
      if (isSending) return;
      const current = sessionsRef.current.find((s) => s.id === activeSessionId);
      let sessionId: string;
      if (current && !current.locationReady && current.messages.length === 0) {
        sessionId = current.id;
      } else {
        const session = makeSession();
        sessionId = session.id;
        setSessions((prev) => [session, ...prev]);
        setActiveSessionId(session.id);
      }
      await confirmAddress(sessionId, input);
    },
    [activeSessionId, confirmAddress, isSending],
  );

  const resetLocation = useCallback(() => {
    if (!activeSessionId) return;
    const current = sessionsRef.current.find((s) => s.id === activeSessionId);
    // Keep earlier conversations: start a new chat if this one has messages.
    if (current && current.messages.some((m) => m.role === "user")) {
      createSession();
      return;
    }
    updateSession(activeSessionId, (s) => ({
      ...s,
      title: "New planning chat",
      propertyFacts: {},
      locationReady: false,
      messages: [],
      updatedAt: new Date().toISOString(),
    }));
  }, [activeSessionId, createSession, updateSession]);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      const sessionId = activeSessionId;
      const current = sessionsRef.current.find((s) => s.id === sessionId);
      if (!trimmed || !sessionId || isSending || !current?.locationReady) {
        return;
      }

      const userMessage: ChatMessage = {
        id: uid(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
      };

      updateSession(sessionId, (s) => {
        const isFirstUser = !s.messages.some((m) => m.role === "user");
        return {
          ...s,
          title: isFirstUser ? titleFromPrompt(trimmed) : s.title,
          messages: [...s.messages, userMessage],
          updatedAt: new Date().toISOString(),
        };
      });

      setIsSending(true);
      try {
        if (!(await ensureConnected())) {
          connect();
          appendAssistant(sessionId, offlineMessage(), { kind: "error" });
          return;
        }
        const replyPromise = waitForSocketReply(sessionId);
        send({
          type: "chat.send",
          sessionId,
          content: trimmed,
          address: current.propertyFacts.address,
          lat: current.propertyFacts.lat,
          lng: current.propertyFacts.lng,
        });
        const reply = await replyPromise;
        appendAssistant(sessionId, reply.content, {
          citations: reply.citations,
          facts: factsFromEvent(reply),
        });
      } catch (error) {
        appendAssistant(
          sessionId,
          error instanceof Error && error.message
            ? error.message
            : "Something went wrong while answering. Please try again.",
          { kind: "error" },
        );
      } finally {
        setIsSending(false);
      }
    },
    [
      activeSessionId,
      appendAssistant,
      connect,
      ensureConnected,
      isSending,
      send,
      updateSession,
      waitForSocketReply,
    ],
  );

  const value: ChatContextValue = {
    sessions,
    activeSessionId,
    activeSession,
    isSidebarOpen,
    isSending,
    hydrated,
    createSession,
    selectSession,
    deleteSession,
    startChatWithAddress,
    startNewChatWithAddress,
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
