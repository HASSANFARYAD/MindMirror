"use client";

import { MessageSquareText, Mic, Pencil, Plus, Search, Send, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  createChatThread,
  deleteChatThread,
  getChatThread,
  listChatThreads,
  renameChatThread,
  streamChatMessage,
  transcribeVoice,
  type ChatMessage,
  type ChatThreadDetail,
  type ChatThreadSummary,
} from "@/lib/api";
import { moodLabelFromText } from "@/lib/sentiment";

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

const starterMessage = "I'm here with you. We can slow this down together, notice what's happening, and find one small next step.";
const TITLE_LIMIT = 48;

function formatThreadTitle(text: string): string {
  const normalized = text.trim().replace(/\s+/g, " ");
  return normalized ? normalized.slice(0, TITLE_LIMIT) : "New chat";
}

function journalTitle(initialJournalContext?: string | null): string {
  return "Journal follow-up";
}

function makeMessage(params: {
  userId: string;
  threadId: string;
  role: "user" | "assistant";
  content: string;
}): ChatMessage {
  return {
    id: crypto.randomUUID(),
    user_id: params.userId,
    thread_id: params.threadId,
    role: params.role,
    content: params.content,
  };
}

export function ChatWindow({ userId, journalEntryId, initialJournalContext }: ChatWindowProps) {
  const [threads, setThreads] = useState<ChatThreadSummary[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [activeThread, setActiveThread] = useState<ChatThreadDetail | null>(null);
  const [search, setSearch] = useState("");
  const [showJournalOnly, setShowJournalOnly] = useState(true);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingThread, setLoadingThread] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  const [input, setInput] = useState(initialJournalContext ? `About this entry: ${initialJournalContext}` : "");
  const [isSending, setIsSending] = useState(false);
  const [currentMood, setCurrentMood] = useState("balanced");
  const [recording, setRecording] = useState(false);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const journalBootstrappedRef = useRef<string | null>(null);

  const messages = activeThread?.messages ?? [];
  const activeThreadSummary = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId) ?? null,
    [threads, activeThreadId],
  );

  async function refreshThreads(nextSearch = search, nextJournalOnly = showJournalOnly) {
    setLoadingThreads(true);
    setSidebarError(null);
    try {
      const list = await listChatThreads(userId, {
        search: nextSearch.trim() || undefined,
        journalOnly: nextJournalOnly,
      });
      setThreads(list);
      return list;
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to load chat history.");
      setThreads([]);
      return [];
    } finally {
      setLoadingThreads(false);
    }
  }

  async function loadThread(threadId: string) {
    setLoadingThread(true);
    setSidebarError(null);
    try {
      const detail = await getChatThread(threadId, userId);
      setActiveThread(detail);
      setActiveThreadId(threadId);
      const latestUserMessage = [...detail.messages].reverse().find((message) => message.role === "user");
      if (latestUserMessage) {
        setCurrentMood(moodLabelFromText(latestUserMessage.content));
      } else if (detail.journal_entry_id) {
        setCurrentMood("balanced");
      }
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to open conversation.");
    } finally {
      setLoadingThread(false);
    }
  }

  async function createAndOpenThread(title: string, threadJournalEntryId?: string | null, initialMessage?: string) {
    const created = await createChatThread({
      user_id: userId,
      title,
      journal_entry_id: threadJournalEntryId,
    });
    const starter = initialMessage ? [makeMessage({ userId, threadId: created.id, role: "assistant", content: initialMessage })] : [];
    setThreads((current) => [created, ...current.filter((thread) => thread.id !== created.id)]);
    setActiveThread({
      ...created,
      messages: starter,
    });
    setActiveThreadId(created.id);
    if (threadJournalEntryId) {
      setCurrentMood(moodLabelFromText(initialMessage ?? starterMessage));
    }
    return created.id;
  }

  async function ensureActiveThreadId(): Promise<string> {
    if (activeThreadId) return activeThreadId;
    const title = journalEntryId ? journalTitle(initialJournalContext) : "New chat";
    return createAndOpenThread(title, journalEntryId, journalEntryId ? starterMessage : undefined);
  }

  useEffect(() => {
    void refreshThreads();
  }, [userId, search, showJournalOnly]);

  useEffect(() => {
    if (!journalEntryId || loadingThreads) return;
    if (journalBootstrappedRef.current === journalEntryId) return;

    const journalThread = threads.find((thread) => thread.journal_entry_id === journalEntryId);
    if (journalThread) {
      journalBootstrappedRef.current = journalEntryId;
      if (journalThread.id !== activeThreadId) {
        void loadThread(journalThread.id);
      }
      return;
    }

    journalBootstrappedRef.current = journalEntryId;
    void (async () => {
      try {
        const createdId = await createAndOpenThread(journalTitle(initialJournalContext), journalEntryId, starterMessage);
        void refreshThreads(search, showJournalOnly);
        if (activeThreadId !== createdId) {
          await loadThread(createdId);
        }
      } catch (error) {
        setSidebarError(error instanceof Error ? error.message : "Failed to prepare journal thread.");
      }
    })();
  }, [activeThreadId, initialJournalContext, journalEntryId, loadingThreads, threads]);

  useEffect(() => {
    viewportRef.current?.scrollTo({ top: viewportRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const activeMessages = messages;
    if (activeMessages.length === 0) {
      if (initialJournalContext) {
        setCurrentMood(moodLabelFromText(initialJournalContext));
      }
      return;
    }

    const latestUserMessage = [...activeMessages].reverse().find((message) => message.role === "user");
    if (latestUserMessage) {
      setCurrentMood(moodLabelFromText(latestUserMessage.content));
    } else if (initialJournalContext) {
      setCurrentMood(moodLabelFromText(initialJournalContext));
    }
  }, [initialJournalContext, messages]);

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
    setSidebarError(null);

    try {
      const threadId = await ensureActiveThreadId();
      const baseMessages = activeThread?.messages ?? [];
      const nextMessages: ChatMessage[] = [
        ...baseMessages,
        makeMessage({ userId, threadId, role: "user", content: trimmed }),
        makeMessage({ userId, threadId, role: "assistant", content: "" }),
      ];

      setActiveThread((current) =>
        current && current.id === threadId ? { ...current, messages: nextMessages } : current,
      );
      setInput("");
      setCurrentMood(moodLabelFromText(trimmed));

      const shouldAutoTitle =
        !journalEntryId &&
        ((activeThreadSummary?.title === "New chat" && (activeThreadSummary.message_count ?? 0) === 0) ||
          !activeThreadSummary);
      if (shouldAutoTitle) {
        const nextTitle = formatThreadTitle(trimmed);
        const renamed = await renameChatThread({ thread_id: threadId, user_id: userId, title: nextTitle });
        setThreads((current) => current.map((thread) => (thread.id === threadId ? { ...thread, ...renamed } : thread)));
        setActiveThread((current) => (current && current.id === threadId ? { ...current, ...renamed } : current));
      }

      let assistantText = "";
      await streamChatMessage(
        {
          user_id: userId,
          thread_id: threadId,
          message: trimmed,
          journal_entry_id: journalEntryId ?? undefined,
        },
        (token) => {
          assistantText += token;
          const streamedMessages: ChatMessage[] = [
            ...baseMessages,
            {
              ...nextMessages[baseMessages.length],
              content: trimmed,
            },
            {
              ...nextMessages[baseMessages.length + 1],
              content: assistantText,
            },
          ];
          setActiveThread((current) =>
            current && current.id === threadId ? { ...current, messages: streamedMessages } : current,
          );
          setCurrentMood(moodLabelFromText(assistantText));
        },
      );

      const refreshed = await getChatThread(threadId, userId);
      setActiveThread(refreshed);
      setThreads(await listChatThreads(userId, { search: search.trim() || undefined, journalOnly: showJournalOnly }));
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to send message.");
      if (activeThreadId) {
        const refreshed = await getChatThread(activeThreadId, userId).catch(() => null);
        if (refreshed) {
          setActiveThread(refreshed);
        }
      }
    } finally {
      setIsSending(false);
    }
  }

  async function handleSelectThread(threadId: string) {
    await loadThread(threadId);
  }

  async function handleRenameThread(thread: ChatThreadSummary) {
    const nextTitle = window.prompt("Rename conversation", thread.title)?.trim();
    if (!nextTitle) return;
    try {
      const updated = await renameChatThread({
        thread_id: thread.id,
        user_id: userId,
        title: nextTitle.slice(0, TITLE_LIMIT),
      });
      setThreads((current) => current.map((item) => (item.id === thread.id ? { ...item, ...updated } : item)));
      if (activeThreadId === thread.id) {
        setActiveThread((current) => (current ? { ...current, ...updated } : current));
      }
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to rename conversation.");
    }
  }

  async function handleDeleteThread(thread: ChatThreadSummary) {
    if (!window.confirm(`Delete "${thread.title}"?`)) return;
    try {
      await deleteChatThread(thread.id, userId);
      const nextThreads = await refreshThreads();
      if (activeThreadId === thread.id) {
        setActiveThread(null);
        setActiveThreadId(null);
        if (nextThreads.length > 0) {
          await loadThread(nextThreads[0].id);
        } else if (!journalEntryId) {
          await createAndOpenThread("New chat", null, starterMessage);
        }
      }
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to delete conversation.");
    }
  }

  async function startNewChat() {
    try {
      const emptyDraft = threads.find(
        (thread) => (thread.title === "New chat" || thread.title === "Journal follow-up") && (thread.message_count ?? 0) === 0,
      );
      if (emptyDraft) {
        await loadThread(emptyDraft.id);
        setInput("");
        setCurrentMood("balanced");
        setShowJournalOnly(false);
        return;
      }

      const created = await createChatThread({ user_id: userId, title: "New chat" });
      setThreads((current) => [created, ...current.filter((thread) => thread.id !== created.id)]);
      setActiveThread({ ...created, messages: [] });
      setActiveThreadId(created.id);
      setInput("");
      setCurrentMood("balanced");
      setShowJournalOnly(false);
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to start a new chat.");
    }
  }

  const visibleThreads = threads;

  return (
    <div className="mx-auto grid h-full min-h-0 w-full max-w-[1280px] gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="surface-card surface-card-hover flex h-full min-h-0 w-full flex-col overflow-hidden rounded-2xl p-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-base font-semibold text-mindmirror-primary">Chat history</p>
            <p className="text-sm text-mindmirror-secondary">Synced to your account and available on any device.</p>
          </div>
          <button
            type="button"
            onClick={startNewChat}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.04)] text-mindmirror-primary transition duration-200 ease-out hover:border-[rgba(255,255,255,0.28)]"
            aria-label="Start new chat"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3">
          <label className="flex items-center gap-2 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] px-3 py-2">
            <Search className="h-4 w-4 text-mindmirror-muted" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search chats"
              className="w-full bg-transparent text-sm text-mindmirror-primary outline-none placeholder:text-mindmirror-muted"
            />
          </label>

          <button
            type="button"
            onClick={() => setShowJournalOnly((current) => !current)}
            className="inline-flex w-full items-center justify-center rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.04)] px-4 py-2 text-sm text-mindmirror-secondary transition duration-200 ease-out hover:border-[rgba(255,255,255,0.22)] hover:text-mindmirror-primary"
          >
            {showJournalOnly ? "Showing journal-linked only" : "Showing all chats"}
          </button>
        </div>

        <div className="mt-4 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {loadingThreads ? (
            <div className="rounded-2xl border border-dashed border-[rgba(255,255,255,0.10)] p-4 text-sm text-mindmirror-muted">
              Loading conversations...
            </div>
          ) : visibleThreads.length ? (
            visibleThreads.map((thread) => {
              const isActive = thread.id === activeThreadId;
              return (
                <div
                  key={thread.id}
                  className={`rounded-2xl border p-3 transition duration-200 ease-out ${
                    isActive
                      ? "border-[rgba(124,58,237,0.45)] bg-[rgba(124,58,237,0.12)]"
                      : "border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)]"
                  }`}
                >
                  <button type="button" onClick={() => void handleSelectThread(thread.id)} className="w-full text-left">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[rgba(139,92,246,0.15)] text-mindmirror-lavender">
                        <MessageSquareText className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-sm font-semibold text-mindmirror-primary">{thread.title}</p>
                          <span className="shrink-0 text-[11px] text-mindmirror-muted">
                            {thread.last_activity_at
                              ? new Date(thread.last_activity_at).toLocaleDateString("en-US", {
                                  month: "short",
                                  day: "numeric",
                                })
                              : ""}
                          </span>
                        </div>
                        <p className="mt-1 truncate text-xs text-mindmirror-secondary">
                          {thread.last_message_preview || "No messages yet"}
                        </p>
                      </div>
                    </div>
                  </button>
                  <div className="mt-3 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => void handleRenameThread(thread)}
                      className="inline-flex items-center gap-1 rounded-full border border-[rgba(255,255,255,0.10)] bg-transparent px-3 py-1.5 text-xs text-mindmirror-secondary transition duration-200 ease-out hover:border-[rgba(255,255,255,0.25)] hover:text-mindmirror-primary"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Rename
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDeleteThread(thread)}
                      className="inline-flex items-center gap-1 rounded-full border border-[rgba(255,255,255,0.10)] bg-transparent px-3 py-1.5 text-xs text-mindmirror-secondary transition duration-200 ease-out hover:border-[rgba(236,72,153,0.35)] hover:text-[#F9A8D4]"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="rounded-2xl border border-dashed border-[rgba(255,255,255,0.10)] p-4 text-sm text-mindmirror-muted">
              {showJournalOnly
                ? "No journal-linked conversations yet. Switch to all chats or open a journal entry."
                : "No conversations yet."}
            </div>
          )}
        </div>

        {sidebarError ? <p className="mt-4 text-sm text-[#FCA5A5]">{sidebarError}</p> : null}
      </aside>

      <section className="surface-card surface-card-hover flex h-full min-w-0 min-h-0 w-full flex-col overflow-hidden rounded-2xl p-4 sm:p-6">
        <div className="mb-4 flex items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-4">
          <div>
            <h2 className="text-2xl font-semibold text-mindmirror-primary">MindMirror</h2>
            <p className="text-sm text-mindmirror-secondary">A calm CBT companion for reflection and reframing.</p>
          </div>
          <div className="rounded-full border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] px-4 py-2 text-sm text-mindmirror-secondary">
            Current mood: <span className="text-[#F9A8D4]">{currentMood}</span>
          </div>
        </div>

        <div ref={viewportRef} className="scrollbar-hide min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
          {loadingThread ? (
            <div className="rounded-2xl border border-dashed border-[rgba(255,255,255,0.10)] p-4 text-sm text-mindmirror-muted">
              Loading conversation...
            </div>
          ) : messages.length ? (
            messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
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
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-[rgba(255,255,255,0.10)] p-6 text-sm text-mindmirror-secondary">
              Start a conversation or select a thread from the sidebar.
            </div>
          )}
          {isSending ? (
            <div className="flex items-center gap-2 text-sm text-mindmirror-muted">
              <span className="h-2 w-2 animate-pulse rounded-full bg-mindmirror-pink" />
              MindMirror is responding...
            </div>
          ) : null}
        </div>

        <div className="mt-4 flex shrink-0 flex-col gap-4">
          <div className="flex flex-wrap gap-2">
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

          <div className="flex flex-col gap-3 sm:flex-row">
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
        </div>
      </section>
    </div>
  );
}
