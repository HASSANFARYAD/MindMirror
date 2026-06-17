"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGate } from "@/components/AuthGate";
import { ChatWindow } from "@/components/ChatWindow";
import { getSessionUserId } from "@/lib/auth";

function ChatPageContent() {
  const params = useSearchParams();
  const entry = params.get("entry");
  const userId = useMemo(() => getSessionUserId(), []);

  return (
    <ChatWindow
      userId={userId}
      journalEntryId={entry}
      initialJournalContext={entry ? "I'd like help understanding this entry." : undefined}
    />
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="page-shell text-sm text-mindmirror-secondary">Loading chat...</div>}>
      <AuthGate>
        <div className="page-shell h-full min-h-0">
          <ChatPageContent />
        </div>
      </AuthGate>
    </Suspense>
  );
}
