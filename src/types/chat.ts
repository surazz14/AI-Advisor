export type MessageRole = "user" | "assistant";

export type Citation = {
  doc: string;
  clause?: string;
  quote?: string;
  page?: string;
  url?: string;
  topic?: string;
  location?: string;
};

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  citations?: Citation[];
};

export type PropertyFacts = {
  address?: string;
  lat?: number;
  lng?: number;
};

export type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  propertyFacts: PropertyFacts;
  /** Chat unlocks only after an address is set */
  locationReady: boolean;
  updatedAt: string;
};

export function displayLocation(facts: PropertyFacts): string {
  return facts.address?.trim() || "";
}
