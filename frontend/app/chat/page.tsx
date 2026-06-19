"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGate } from "@/components/AuthGate";
import { ChatWindow } from "@/components/ChatWindow";

function ChatPageContent() {
  const params = useSearchParams();
  const entry = params.get("entry");
  const [bannerVisible, setBannerVisible] = useState(true);

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      {bannerVisible ? (
        <div
          className="flex items-start justify-between gap-4 rounded-lg border border-[rgba(255,179,71,0.3)] bg-[rgba(255,179,71,0.1)] px-4 py-3 text-sm text-mindmirror-primary"
          role="status"
        >
          <p>
            🧡 MindMirror supports your reflection but is not a crisis service. If you&apos;re in distress, please contact a
            mental health helpline.
          </p>
          <button
            type="button"
            aria-label="Dismiss safety banner"
            className="text-lg leading-none text-mindmirror-secondary transition hover:text-mindmirror-primary"
            onClick={() => {
              setBannerVisible(false);
            }}
          >
            ×
          </button>
        </div>
      ) : null}
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
