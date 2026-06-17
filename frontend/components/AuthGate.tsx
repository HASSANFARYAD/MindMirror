"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getStoredSession, refreshSession, type AuthSession } from "@/lib/auth";

type AuthGateProps = {
  children: ReactNode;
};

function buildLoginUrl(target: string): string {
  return `/login?next=${encodeURIComponent(target)}`;
}

export function AuthGate({ children }: AuthGateProps) {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null | undefined>(undefined);

  useEffect(() => {
    let active = true;

    async function hydrate() {
      const target = `${window.location.pathname}${window.location.search}`;
      const existing = getStoredSession();

      if (!existing) {
        if (active) {
          setSession(null);
          router.replace(buildLoginUrl(target));
        }
        return;
      }

      const refreshed = await refreshSession().catch(() => null);
      if (!active) return;

      if (!refreshed) {
        clearSession();
        setSession(null);
        router.replace(buildLoginUrl(target));
        return;
      }

      setSession(refreshed);
    }

    void hydrate();

    return () => {
      active = false;
    };
  }, [router]);

  if (session === undefined) {
    return <div className="text-sm text-white/55">Checking session...</div>;
  }

  if (!session) {
    return null;
  }

  return <>{children}</>;
}
