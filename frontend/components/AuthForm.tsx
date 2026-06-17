"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowRight, CircleCheckBig, LogIn, UserPlus } from "lucide-react";
import {
  clearSession,
  getStoredSession,
  loginWithJwt,
  refreshSession,
  registerWithJwt,
  saveSession,
  type AuthSession,
} from "@/lib/auth";

type AuthMode = "login" | "signup";

type AuthFormProps = {
  mode: AuthMode;
};

function resolveRedirectTarget(target: string | null): string {
  if (!target || !target.startsWith("/")) return "/dashboard";
  return target;
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const params = useSearchParams();
  const redirectTarget = useMemo(() => resolveRedirectTarget(params.get("next")), [params]);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function hydrate() {
      try {
        const existing = getStoredSession();
        if (!existing) return;
        const refreshed = await refreshSession();
        if (!active) return;
        setSession(refreshed ?? existing);
      } finally {
        if (active) setLoading(false);
      }
    }

    void hydrate();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!session) return;
    router.replace(redirectTarget);
  }, [redirectTarget, router, session]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      email: email.trim(),
      name: name.trim() || undefined,
      password: password.trim() || undefined,
    };

    try {
      const nextSession = mode === "login" ? await loginWithJwt(payload) : await registerWithJwt(payload);
      saveSession(nextSession);
      setSession(nextSession);
      router.replace(redirectTarget);
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
      <div className="space-y-6">
        <div className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/75">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            {mode === "login" ? "Sign in with your JWT session" : "Join MindMirror in a few seconds"}
          </h1>
          <p className="max-w-xl text-base leading-7 text-white/65">
            {mode === "login"
              ? "Use the existing backend auth route to mint a JWT and restore your saved session locally."
              : "Create a profile, receive a JWT from the backend, and continue into the app immediately."}
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            ["JWT token", "Stored locally for the browser session."],
            ["/auth/me", "Used to refresh the signed-in user."],
            ["FastAPI", "Backed by the existing auth routes."],
          ].map(([title, description]) => (
            <article key={title} className="glass-card rounded-[1.5rem] p-4">
              <p className="text-sm font-medium text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-white/55">{description}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-[2rem] p-5 shadow-glow sm:p-7">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold text-white">{mode === "login" ? "Log in" : "Sign up"}</h2>
            <p className="text-sm text-white/55">
              {mode === "login"
                ? "Enter the email associated with your saved MindMirror profile."
                : "Create a new profile with email and display name."}
            </p>
          </div>
          <div className="rounded-2xl bg-white/5 p-3 text-mindmirror-violet">
            {mode === "login" ? <LogIn className="h-5 w-5" /> : <UserPlus className="h-5 w-5" />}
          </div>
        </div>

        <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
          <label className="block space-y-2">
            <span className="text-sm text-white/70">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-2xl border border-white/8 bg-[#111120] px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-mindmirror-violet/60"
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm text-white/70">Display name {mode === "signup" ? "" : "(optional)"}</span>
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder={mode === "signup" ? "Ava" : "Leave blank to reuse your saved profile"}
              required={mode === "signup"}
              className="w-full rounded-2xl border border-white/8 bg-[#111120] px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-mindmirror-violet/60"
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm text-white/70">Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Optional for the current backend setup"
              className="w-full rounded-2xl border border-white/8 bg-[#111120] px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-mindmirror-violet/60"
            />
          </label>

          <button
            type="submit"
            disabled={submitting || loading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-mindmirror-violet px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Working..." : mode === "login" ? "Log in" : "Create account"}
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}

        {session ? (
          <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-200">
            <div className="flex items-center gap-2 font-medium">
              <CircleCheckBig className="h-4 w-4" />
              Signed in as {session.user.email}
            </div>
            <p className="mt-1 text-emerald-100/80">Redirecting to your workspace...</p>
          </div>
        ) : null}

        <div className="mt-6 flex items-center justify-between border-t border-white/8 pt-4 text-sm text-white/55">
          <span>{mode === "login" ? "Need a new profile?" : "Already have an account?"}</span>
          <Link
            href={mode === "login" ? "/signup" : "/login"}
            className="inline-flex items-center gap-1 text-white transition hover:text-mindmirror-pink"
          >
            {mode === "login" ? "Go to signup" : "Go to login"}
          </Link>
        </div>

        <button
          type="button"
          onClick={() => {
            clearSession();
            setSession(null);
            setEmail("");
            setName("");
            setPassword("");
          }}
          className="mt-3 text-xs text-white/40 transition hover:text-white/70"
        >
          Clear local session
        </button>
      </div>
    </section>
  );
}
