"use client";

import { Mic, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getJournalEntry, streamChatMessage, transcribeVoice } from "@/lib/api";
import { moodLabelFromText } from "@/lib/sentiment";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ChatWindowProps = {
  userId: string;
  journalEntryId?: string | null;
  initialJournalContext?: string | null;
};

const quickReplies = [
  "I'm feeling anxious",
  "I had a bad day",
  "I need to vent",
  "Help me reframe a thought",
];

export function ChatWindow({ userId, journalEntryId, initialJournalContext }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "I'm here with you. We can slow this down together, notice what's happening, and find one small next step.",
    },
  ]);
  const [input, setInput] = useState(initialJournalContext ? `About this entry: ${initialJournalContext}` : "");
  const [isSending, setIsSending] = useState(false);
  const [currentMood, setCurrentMood] = useState("balanced");
  const [recording, setRecording] = useState(false);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    viewportRef.current?.scrollTo({ top: viewportRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let active = true;

    async function hydrateJournalMood() {
      if (journalEntryId) {
        const entry = await getJournalEntry(journalEntryId).catch(() => null);
        if (!active || !entry) return;

        if (typeof entry.sentiment_score === "number") {
          setCurrentMood(entry.sentiment_score > 0.35 ? "uplifted" : entry.sentiment_score > 0.1 ? "steady" : entry.sentiment_score < -0.35 ? "heavy" : entry.sentiment_score < -0.1 ? "uneasy" : "balanced");
          return;
        }

        if (entry.content) {
          setCurrentMood(moodLabelFromText(entry.content));
        }
        return;
      }

      if (initialJournalContext) {
        setCurrentMood(moodLabelFromText(initialJournalContext));
      } else {
        setCurrentMood("balanced");
      }
    }

    void hydrateJournalMood();

    return () => {
      active = false;
    };
  }, [initialJournalContext, journalEntryId]);

  async function toggleVoice() {
    if (recording) {
      recorderRef.current?.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        setVoiceBusy(true);
        try {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const transcript = await transcribeVoice(blob);
          setInput((current) => `${current} ${transcript}`.trim());
        } finally {
          setVoiceBusy(false);
        }
      };

      recorder.start();
      setRecording(true);
    } catch {
      setVoiceBusy(false);
      setRecording(false);
    }
  }

  async function handleSend(content: string) {
    const trimmed = content.trim();
    if (!trimmed || isSending) return;

    setIsSending(true);
    setMessages((current) => [...current, { role: "user", content: trimmed }, { role: "assistant", content: "" }]);
    setInput("");
    setCurrentMood(moodLabelFromText(trimmed));

    try {
      let assistantText = "";
      await streamChatMessage(
        { user_id: userId, message: trimmed, journal_entry_id: journalEntryId ?? undefined },
        (token) => {
          assistantText += token;
          setMessages((current) => {
            const next = [...current];
            const lastIndex = next.length - 1;
            if (lastIndex >= 0 && next[lastIndex]?.role === "assistant") {
              next[lastIndex] = { role: "assistant", content: assistantText };
            }
            return next;
          });
          setCurrentMood(moodLabelFromText(assistantText));
        },
      );
    } catch (error) {
      setMessages((current) => {
        const next = [...current];
        const lastIndex = next.length - 1;
        if (lastIndex >= 0 && next[lastIndex]?.role === "assistant") {
          next[lastIndex] = {
            role: "assistant",
            content: error instanceof Error ? error.message : "Something went wrong while generating a reply.",
          };
        }
        return next;
      });
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="surface-card surface-card-hover mx-auto flex w-full max-w-[960px] min-h-[75vh] flex-col rounded-2xl p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-4">
        <div>
          <h2 className="text-2xl font-semibold text-mindmirror-primary">MindMirror</h2>
          <p className="text-sm text-mindmirror-secondary">A calm CBT companion for reflection and reframing.</p>
        </div>
        <div className="rounded-full border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] px-4 py-2 text-sm text-mindmirror-secondary">
          Current mood: <span className="text-[#F9A8D4]">{currentMood}</span>
        </div>
      </div>

      <div ref={viewportRef} className="scrollbar-hide flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[82%] rounded-[1.5rem] px-4 py-3 text-sm leading-6 sm:max-w-[70%] ${
                message.role === "user"
                  ? "bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] text-mindmirror-primary"
                  : "border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] text-mindmirror-primary"
              }`}
            >
              {message.role === "assistant" ? (
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#EC4899_100%)] text-xs font-bold text-mindmirror-primary">
                    MM
                  </div>
                  <p className="pt-1 text-mindmirror-secondary">{message.content || (isSending ? "Thinking..." : "")}</p>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
            </div>
          </div>
        ))}
        {isSending ? (
          <div className="flex items-center gap-2 text-sm text-mindmirror-muted">
            <span className="h-2 w-2 animate-pulse rounded-full bg-mindmirror-pink" />
            MindMirror is responding...
          </div>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {quickReplies.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => setInput(chip)}
            className="rounded-full border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] px-3 py-2 text-xs text-mindmirror-secondary transition duration-200 ease-out hover:border-[rgba(255,255,255,0.18)] hover:text-mindmirror-primary"
          >
            {chip}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={() => void toggleVoice()}
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.04)] px-4 py-3 text-sm text-mindmirror-primary transition duration-[180ms] ease-out hover:border-[rgba(255,255,255,0.25)]"
        >
          <Mic className={`h-4 w-4 ${recording ? "text-mindmirror-pink" : "text-mindmirror-secondary"}`} />
          {voiceBusy ? "Transcribing" : recording ? "Stop" : "Voice"}
        </button>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type a message or choose a quick reply..."
          className="min-h-[56px] flex-1 resize-none rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-mindmirror-primary outline-none placeholder:text-mindmirror-muted focus:border-[rgba(124,58,237,0.6)]"
        />
        <button
          type="button"
          onClick={() => void handleSend(input)}
          disabled={isSending}
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-5 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] disabled:opacity-60"
        >
          <Send className="h-4 w-4" />
          Send
        </button>
      </div>
    </section>
  );
}
