export type MessageRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
};

export type PropertyFacts = {
  address?: string;
  zone?: string;
  bushfireProne?: boolean | null;
  locality?: string;
  areaM2?: number | null;
};

export type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  propertyFacts: PropertyFacts;
  updatedAt: string;
};
