"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, Mail, X, Loader2, CheckCircle } from "lucide-react";
import { getStoredSession } from "@/lib/auth";
import { sendVerificationEmail } from "@/lib/api";

export function EmailVerificationBanner() {
  const [session, setSession] = useState(getStoredSession());
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const onAuth = () => setSession(getStoredSession());
    window.addEventListener("mindmirror-auth-change", onAuth);
    return () => window.removeEventListener("mindmirror-auth-change", onAuth);
  }, []);

  if (!session || session.user.email_verified || dismissed) return null;

  const handleSend = async () => {
    setSending(true);
    try {
      await sendVerificationEmail();
      setSent(true);
    } catch {
      /* silent — banner remains */
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl items-center gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-amber-200">
      {sent ? (
        <CheckCircle className="h-5 w-5 shrink-0 text-emerald-400" />
      ) : (
        <AlertTriangle className="h-5 w-5 shrink-0 text-amber-400" />
      )}
      <p className="flex-1 text-sm">
        {sent
          ? "Verification email sent! Check your inbox."
          : "Please verify your email address to secure your account."}
      </p>
      {!sent && (
        <button
          onClick={handleSend}
          disabled={sending}
          className="flex items-center gap-1.5 rounded-lg bg-amber-500/20 px-3 py-1.5 text-sm font-medium text-amber-200 transition-colors hover:bg-amber-500/30 disabled:opacity-50"
        >
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Mail className="h-4 w-4" />
          )}
          {sending ? "Sending..." : "Send verification"}
        </button>
      )}
      <button
        onClick={() => setDismissed(true)}
        className="shrink-0 rounded p-1 text-amber-400/60 transition-colors hover:text-amber-200"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
