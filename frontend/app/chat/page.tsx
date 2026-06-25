"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGate } from "@/components/AuthGate";
import { ChatWindow } from "@/components/ChatWindow";

function ChatPageContent() {
  const params = useSearchParams();
  const entry = params.get("entry");

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ChatWindow journalEntryId={entry} initialJournalContext={entry ? "I'd like help understanding this entry." : undefined} />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="page-shell text-sm text-mindmirror-secondary">Loading chat...</div>}>
      <AuthGate>
        <div className="page-shell flex h-full min-h-0 flex-col">
          <ChatPageContent />
        </div>
      </AuthGate>
    </Suspense>
  );
}
