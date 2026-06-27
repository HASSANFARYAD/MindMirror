"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { getStoredSession, onAuthChange, refreshSession, type AuthSession } from "@/lib/auth";
import { PushManager } from "@/components/PushManager";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/journal", label: "Journal" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/export", label: "Export for Therapist" },
  { href: "/chat", label: "Chat" },
];

function appendDemoQuery(href: string, enabled: boolean): string {
  if (!enabled || href.includes("demo=true")) return href;
  return href.includes("?") ? `${href}&demo=true` : `${href}?demo=true`;
}

export function SiteHeader() {
  const searchParams = useSearchParams();
  const [session, setSession] = useState<AuthSession | null>(null);
  const visibleNavItems = session ? navItems : navItems.slice(0, 1);
  const preserveDemo = searchParams.get("demo") === "true";

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
        </div>

        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-end">
          <nav className="flex flex-wrap items-center gap-4 sm:gap-6">
            {visibleNavItems.map((item) => (
              <Link
                key={item.href}
                href={appendDemoQuery(item.href, preserveDemo)}
                className="rounded-full px-4 py-2 text-sm text-mindmirror-secondary transition-colors duration-200 ease-out hover:text-mindmirror-primary"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2 md:justify-end">
            {session ? (
              <div className="flex items-center gap-2">
              <PushManager />
              <a
                href="/logout"
                className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.05)] px-4 py-2 text-sm text-mindmirror-secondary transition-colors duration-200 ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </a>
              </div>
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
