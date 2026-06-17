"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getStoredSession, onAuthChange } from "@/lib/auth";

type HomeActionsProps = {
  primaryLabel?: string;
  secondaryLabel?: string;
};

function buildAuthHref(basePath: "/login" | "/signup", nextPath: string): string {
  return `${basePath}?next=${encodeURIComponent(nextPath)}`;
}

export function HomeActions({ primaryLabel = "Create Account", secondaryLabel = "Log In" }: HomeActionsProps) {
  const [isSignedIn, setIsSignedIn] = useState(false);

  useEffect(() => {
    setIsSignedIn(Boolean(getStoredSession()));

    function handleStorage() {
      setIsSignedIn(Boolean(getStoredSession()));
    }

    window.addEventListener("storage", handleStorage);
    const unsubscribe = onAuthChange(handleStorage);
    return () => {
      window.removeEventListener("storage", handleStorage);
      unsubscribe();
    };
  }, []);

  const primaryHref = isSignedIn ? "/journal" : buildAuthHref("/signup", "/journal");
  const secondaryHref = isSignedIn ? "/dashboard" : buildAuthHref("/login", "/dashboard");

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <Link
        href={primaryHref}
        className="inline-flex cursor-pointer items-center justify-center rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-7 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)]"
      >
        {isSignedIn ? "Open Journal" : primaryLabel}
      </Link>
      <Link
        href={secondaryHref}
        className="inline-flex cursor-pointer items-center justify-center rounded-full border border-[rgba(255,255,255,0.15)] bg-transparent px-7 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:border-[rgba(255,255,255,0.35)]"
      >
        {isSignedIn ? "View Dashboard" : secondaryLabel}
      </Link>
    </div>
  );
}
