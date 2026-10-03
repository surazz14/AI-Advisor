import { Suspense } from "react";
import { ChatShell } from "@/components/chat/ChatShell";

export default function ChatPage() {
  // ChatShell reads ?ask= with useSearchParams, which needs a Suspense boundary.
  return (
    <Suspense fallback={null}>
      <ChatShell />
    </Suspense>
  );
}
