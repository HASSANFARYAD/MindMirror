"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { getStoredSession, onAuthChange, refreshSession, type AuthSession } from "@/lib/auth";

const DEMO_EMAIL = "demo@mindmirror.app";

function appendDemoQuery(href: string): string {
  if (href.includes("demo=true")) return href;
  return href.includes("?") ? `${href}&demo=true` : `${href}?demo=true`;
}

export function DemoBanner() {
  const searchParams = useSearchParams();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let active = true;

    async function hydrate() {
      const existing = getStoredSession();
      if (!existing) {
        if (active) {
          setSession(null);
          setHydrated(true);
        }
        return;
      }

      const refreshed = await refreshSession().catch(() => null);
      if (!active) return;
      setSession(refreshed ?? existing);
      setHydrated(true);
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

  const isDemoActive = useMemo(() => searchParams.get("demo") === "true" || session?.user.email === DEMO_EMAIL, [searchParams, session]);

  if (!hydrated || !isDemoActive) {
    return null;
  }

  return (
    <div className="demo-banner fixed inset-x-0 bottom-0 z-50 flex justify-center px-4 pb-3">
      <div className="flex h-11 w-full max-w-[1200px] items-center justify-between gap-3 rounded-full bg-[rgba(108,99,255,0.95)] px-4 shadow-[0_12px_32px_rgba(0,0,0,0.25)] backdrop-blur-[8px] sm:px-5">
        <div className="min-w-0 shrink-0 text-[13px] font-medium text-white">🎬 Demo Mode Active</div>
        <div className="flex items-center gap-2">
          <Link
            href={appendDemoQuery("/journal")}
            className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[11px] font-medium text-white transition hover:bg-white/18"
          >
            📓 Open Journal
          </Link>
          <Link
            href={appendDemoQuery("/chat")}
            className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[11px] font-medium text-white transition hover:bg-white/18"
          >
            🧠 Open Chat
          </Link>
          <Link
            href={appendDemoQuery("/dashboard")}
            className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[11px] font-medium text-white transition hover:bg-white/18"
          >
            📊 Dashboard
          </Link>
        </div>
        <div className="min-w-0 shrink-0 text-[12px] text-white/70">Logged in as Alex (demo)</div>
      </div>
    </div>
  );
}
