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

export type EmotionPreview = {
  dominant_emotion: string;
  sentiment_score: number;
};

export type GrowthStory = {
  show: boolean;
  started: {
    avg_sentiment: number;
    dominant_emotion: string;
    distortion_avg: number;
    entry_count: number;
    top_distortion: string;
  };
  now: {
    avg_sentiment: number;
    dominant_emotion: string;
    distortion_avg: number;
    entry_count: number;
    top_distortion: string;
  };
  summary: string;
};

export type TherapistExportSummary = {
  range_key: string;
  range_label: string;
  date_range_covered: {
    start: string;
    end: string;
  };
  generated_at: string;
  average_sentiment_score: number;
  dominant_emotions: Array<{ emotion: string; count: number }>;
  cognitive_distortions: Array<{ type: string; count: number }>;
  growth_moments_identified: string[];
  weekly_insights_text: string;
  total_journal_entries_analyzed: number;
  therapist_summary: string;
  disclaimer: string;
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

const FETCH_DEFAULTS = { credentials: "include" as const };

function sanitizeTextInput(value: string, label: string, maxLength: number): string {
  const normalized = value.trim();
  if (!normalized) {
    throw new Error(`${label} cannot be empty.`);
  }
  if (normalized.length > maxLength) {
    throw new Error(`${label} must be ${maxLength} characters or fewer.`);
  }
  return normalized;
}

async function readErrorMessage(response: Response): Promise<string> {
  const detail = await response.text();
  try {
    const parsed = JSON.parse(detail) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail;
    }
  } catch {
    // Fall back to the raw response text.
  }
  return detail || `Request failed with status ${response.status}`;
}

function buildHeaders(init?: RequestInit): HeadersInit {
  const headers = new Headers();
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  new Headers(init?.headers ?? {}).forEach((value, key) => {
    headers.set(key, value);
  });
  return headers;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...FETCH_DEFAULTS,
    ...init,
    headers: buildHeaders(init),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<T>;
}

export async function registerDemoUser(email: string, name?: string) {
  return requestJson<{ user: { id: string; email: string; name?: string | null } }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: sanitizeTextInput(email, "Email", 320),
      name: name?.trim() || undefined,
      password: "Demo1234!",
    }),
  });
}

export async function submitJournalEntry(payload: {
  content: string;
  voice_file?: string | null;
}): Promise<JournalEntry> {
  return requestJson<JournalEntry>("/journal/entry", {
    method: "POST",
    body: JSON.stringify({
      content: sanitizeTextInput(payload.content, "Journal content", 10000),
      voice_file: payload.voice_file ?? null,
    }),
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
    credentials: "include",
    headers: buildHeaders({ body: form }),
    body: form,
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  const data = (await response.json()) as { transcript: string };
  return data.transcript;
}

export async function getEmotionalMap(): Promise<{
  timeline: EmotionPoint[];
  radar: Array<{ emotion: string; score: number }>;
  patterns: Array<{ id?: string; pattern_type: string; description: string; severity: string }>;
  growth_story?: GrowthStory | null;
  weekly_insights: Array<{
    id: string;
    dominant_emotion?: string | null;
    avg_sentiment?: number | null;
    top_triggers?: Array<{ term: string; count: number }> | null;
    cbt_recommendation?: string | null;
    week_start?: string | null;
  }>;
}> {
  return requestJson(`/analysis/emotional-map`);
}

export async function previewEmotion(text: string): Promise<EmotionPreview> {
  return requestJson<EmotionPreview>("/analysis/preview", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export async function getTherapistExport(range: "7" | "30" | "all"): Promise<TherapistExportSummary> {
  return requestJson<TherapistExportSummary>(`/analysis/export?range=${encodeURIComponent(range)}`);
}

export async function streamChatMessage(
  payload: { message: string; journal_entry_id?: string | null; thread_id?: string | null },
  onToken: (token: string) => void,
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/chat/message`, {
    method: "POST",
    credentials: "include",
    body: JSON.stringify({
      message: sanitizeTextInput(payload.message, "Chat message", 2000),
      journal_entry_id: payload.journal_entry_id ?? null,
      thread_id: payload.thread_id ?? null,
    }),
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

export async function listChatThreads(options?: { search?: string; journalOnly?: boolean }): Promise<ChatThreadSummary[]> {
  const params = new URLSearchParams();
  if (options?.search) params.set("search", options.search);
  params.set("journal_only", String(options?.journalOnly ?? true));
  return requestJson<ChatThreadSummary[]>(`/chat/threads?${params.toString()}`);
}

export async function createChatThread(payload: {
  title: string;
  journal_entry_id?: string | null;
}): Promise<ChatThreadSummary> {
  return requestJson<ChatThreadSummary>("/chat/threads", {
    method: "POST",
    body: JSON.stringify({
      title: sanitizeTextInput(payload.title, "Chat title", 120),
      journal_entry_id: payload.journal_entry_id ?? null,
    }),
  });
}

export async function getChatThread(threadId: string): Promise<ChatThreadDetail> {
  return requestJson<ChatThreadDetail>(`/chat/threads/${threadId}`);
}

export async function renameChatThread(payload: {
  thread_id: string;
  title: string;
}): Promise<ChatThreadSummary> {
  return requestJson<ChatThreadSummary>(`/chat/threads/${payload.thread_id}`, {
    method: "PATCH",
    body: JSON.stringify({ title: sanitizeTextInput(payload.title, "Chat title", 120) }),
  });
}

export async function deleteChatThread(threadId: string): Promise<void> {
  await requestJson(`/chat/threads/${threadId}`, {
    method: "DELETE",
  });
}

export async function sendVerificationEmail(): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>("/auth/send-verification", {
    method: "POST",
  });
}

export async function verifyEmail(token: string): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(
    `/auth/verify-email?token=${encodeURIComponent(token)}`,
  );
}
