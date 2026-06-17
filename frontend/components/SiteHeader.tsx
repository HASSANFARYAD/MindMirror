"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, Sparkles } from "lucide-react";
import { getStoredSession, onAuthChange, refreshSession, signOutSession, type AuthSession } from "@/lib/auth";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/journal", label: "Journal" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
];

export function SiteHeader() {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const visibleNavItems = session ? navItems : navItems.slice(0, 1);

  useEffect(() => {
    let active = true;

    async function hydrate() {
      const existing = getStoredSession();
      if (!existing) return;

      const refreshed = await refreshSession().catch(() => null);
      if (!active) return;
      setSession(refreshed ?? existing);
    }

    void hydrate();

    const unsubscribe = onAuthChange(() => {
      void hydrate();
    });

    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  return (
    <header
      className="sticky top-0 z-50 border-t border-[rgba(255,255,255,0.06)] bg-[rgba(15,12,28,0.7)] backdrop-blur-[12px]"
    >
      <div className="page-shell flex flex-col gap-4 px-5 py-4 md:px-12 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3 px-4 text-lg font-semibold tracking-wide text-mindmirror-primary">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#7C3AED_0%,#EC4899_100%)] text-sm font-bold text-mindmirror-primary">
              MM
            </span>
            MindMirror
          </Link>
          {session ? (
            <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200 sm:flex">
              <Sparkles className="h-3.5 w-3.5" />
              Signed in as {session.user.email}
            </div>
          ) : null}
        </div>

        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-end">
          <nav className="flex flex-wrap items-center gap-2 sm:gap-3">
            {visibleNavItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-full px-4 py-2 text-sm text-mindmirror-secondary transition-colors duration-200 ease-out hover:text-mindmirror-primary"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex flex-wrap items-center gap-2 md:justify-end">
            {session ? (
              <button
                type="button"
                onClick={() => {
                  signOutSession();
                  setSession(null);
                  router.replace("/");
                  router.refresh();
                }}
                className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.05)] px-4 py-2 text-sm text-mindmirror-secondary transition-colors duration-200 ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.05)] px-4 py-2 text-sm text-mindmirror-secondary transition-colors duration-200 ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
                >
                  Log in
                </Link>
                <Link
                  href="/signup"
                  className="rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-4 py-2 text-sm font-semibold text-mindmirror-primary transition duration-200 ease-out"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
