import { apiBaseUrl } from "@/lib/api";

export type AuthUser = {
  id: string;
  email: string;
  name?: string | null;
};

export type AuthSession = {
  user: AuthUser;
};

const SESSION_STORAGE_KEY = "mindmirror_session";
const ANON_STORAGE_KEY = "mindmirror_user_id";
const AUTH_EVENT_NAME = "mindmirror-auth-change";

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

function hasAuthUser(value: unknown): value is AuthUser {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.id === "string" && typeof candidate.email === "string";
}

function hasAuthSession(value: unknown): value is AuthSession {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return hasAuthUser(candidate.user);
}

export function getStoredSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    return hasAuthSession(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function getAnonymousUserId(): string {
  if (typeof window === "undefined") return "demo-user";
  const existing = window.localStorage.getItem(ANON_STORAGE_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(ANON_STORAGE_KEY, created);
  return created;
}

export function saveSession(session: AuthSession): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  window.dispatchEvent(new Event(AUTH_EVENT_NAME));
}

function persistSession(session: AuthSession): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
  window.dispatchEvent(new Event(AUTH_EVENT_NAME));
}

export function clearAnonymousUserId(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ANON_STORAGE_KEY);
}

export function signOutSession(): void {
  clearSession();
  clearAnonymousUserId();
  // Tell the backend to clear the HttpOnly cookie.
  fetch(`${apiBaseUrl}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => {});
}

export function onAuthChange(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(AUTH_EVENT_NAME, listener);
  return () => window.removeEventListener(AUTH_EVENT_NAME, listener);
}

export function getSessionUserId(fallback = "demo-user"): string {
  return getStoredSession()?.user.id ?? (typeof window === "undefined" ? fallback : getAnonymousUserId());
}

async function authRequest(
  path: "/auth/login" | "/auth/register",
  body: { email: string; name?: string; password: string },
): Promise<AuthSession> {
  const email = body.email.trim();
  const name = body.name?.trim();
  const password = body.password.trim();
  if (!email || !password) {
    throw new Error("Email and password are required.");
  }
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, name: name || undefined, password }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const data = (await response.json()) as { user: AuthUser };
  return { user: data.user };
}

export async function loginWithJwt(body: { email: string; name?: string; password: string }) {
  return authRequest("/auth/login", body);
}

export async function registerWithJwt(body: { email: string; name?: string; password: string }) {
  return authRequest("/auth/register", body);
}

export async function refreshSession(): Promise<AuthSession | null> {
  const session = getStoredSession();
  if (!session?.user) return null;

  const response = await fetch(`${apiBaseUrl}/auth/me`, {
    credentials: "include",
  });

  if (!response.ok) {
    signOutSession();
    return null;
  }

  const user = (await response.json()) as AuthUser;
  const nextSession = { user };
  persistSession(nextSession);
  return nextSession;
}
