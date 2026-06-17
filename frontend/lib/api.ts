export type EmotionPoint = {
  date: string;
  sentiment_score: number;
  dominant_emotion: string;
  emotions: Record<string, number>;
  snippet?: string | null;
};

export type JournalAnalysis = {
  sentiment_score: number;
  sentiment_label: string;
  emotions: Record<string, number>;
  cognitive_distortions: Array<{ type: string; evidence: string; confidence: number }>;
};

export type JournalEntry = {
  id: string;
  user_id: string;
  content: string;
  voice_transcript?: string | null;
  sentiment_score?: number | null;
  sentiment_label?: string | null;
  emotions?: Record<string, number> | null;
  cognitive_distortions?: Array<{ type: string; evidence: string; confidence: number }> | null;
  created_at?: string | null;
};

export type ChatThreadSummary = {
  id: string;
  user_id: string;
  journal_entry_id?: string | null;
  title: string;
  created_at?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  message_count?: number | null;
  last_activity_at?: string | null;
};

export type ChatMessage = {
  id: string;
  user_id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string | null;
};

export type ChatThreadDetail = ChatThreadSummary & {
  messages: ChatMessage[];
};

const apiPort = process.env.NEXT_PUBLIC_API_PORT ?? "8000";
export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? `http://localhost:${apiPort}`;

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function registerDemoUser(email: string, name?: string) {
  return requestJson<{ user: { id: string; email: string; name?: string | null }; token: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name }),
  });
}

export async function submitJournalEntry(payload: {
  user_id: string;
  content: string;
  voice_file?: string | null;
}): Promise<JournalEntry> {
  return requestJson<JournalEntry>("/journal/entry", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getJournalEntry(entryId: string): Promise<JournalEntry> {
  return requestJson<JournalEntry>(`/journal/entry/${entryId}`);
}

export async function transcribeVoice(file: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", file, "voice.webm");
  const response = await fetch(`${apiBaseUrl}/journal/voice-transcribe`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const data = (await response.json()) as { transcript: string };
  return data.transcript;
}

export async function getEmotionalMap(userId: string): Promise<{
  timeline: EmotionPoint[];
  radar: Array<{ emotion: string; score: number }>;
  patterns: Array<{ id?: string; pattern_type: string; description: string; severity: string }>;
  weekly_insights: Array<{
    id: string;
    dominant_emotion?: string | null;
    avg_sentiment?: number | null;
    top_triggers?: Array<{ term: string; count: number }> | null;
    cbt_recommendation?: string | null;
    week_start?: string | null;
  }>;
}> {
  return requestJson(`/analysis/emotional-map/${userId}`);
}

export async function streamChatMessage(
  payload: { user_id: string; message: string; journal_entry_id?: string | null; thread_id?: string | null },
  onToken: (token: string) => void,
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const line = event
        .split("\n")
        .find((part) => part.startsWith("data: "));
      if (!line) continue;
      const data = JSON.parse(line.replace(/^data:\s*/, "")) as { type: string; value?: string };
      if (data.type === "token" && data.value) {
        onToken(data.value);
      }
    }
  }
}

export async function listChatThreads(
  userId: string,
  options?: { search?: string; journalOnly?: boolean },
): Promise<ChatThreadSummary[]> {
  const params = new URLSearchParams({ user_id: userId });
  if (options?.search) params.set("search", options.search);
  params.set("journal_only", String(options?.journalOnly ?? true));
  return requestJson<ChatThreadSummary[]>(`/chat/threads?${params.toString()}`);
}

export async function createChatThread(payload: {
  user_id: string;
  title: string;
  journal_entry_id?: string | null;
}): Promise<ChatThreadSummary> {
  return requestJson<ChatThreadSummary>("/chat/threads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getChatThread(threadId: string, userId: string): Promise<ChatThreadDetail> {
  const params = new URLSearchParams({ user_id: userId });
  return requestJson<ChatThreadDetail>(`/chat/threads/${threadId}?${params.toString()}`);
}

export async function renameChatThread(payload: {
  thread_id: string;
  user_id: string;
  title: string;
}): Promise<ChatThreadSummary> {
  return requestJson<ChatThreadSummary>(`/chat/threads/${payload.thread_id}`, {
    method: "PATCH",
    body: JSON.stringify({ user_id: payload.user_id, title: payload.title }),
  });
}

export async function deleteChatThread(threadId: string, userId: string): Promise<void> {
  await requestJson(`/chat/threads/${threadId}?user_id=${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
}
