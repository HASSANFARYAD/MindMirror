"use client";

import type { ReactNode } from "react";
import { Suspense } from "react";
import { usePathname } from "next/navigation";
import { SiteHeader } from "@/components/SiteHeader";
// import { DemoBanner } from "@/components/DemoBanner";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const isChatRoute = pathname?.startsWith("/chat");

  return (
    <div
      className={`relative flex ${isChatRoute ? "h-dvh overflow-hidden" : "min-h-screen overflow-x-hidden overflow-y-auto"} flex-col bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.16),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(236,72,153,0.12),transparent_22%),linear-gradient(180deg,#0D0B1A_0%,#0D0B1A_100%)]`}
    >
      <Suspense fallback={null}>
        <SiteHeader />
      </Suspense>
      <main
        className={`relative z-10 mx-auto w-full px-5 py-8 pb-20 md:px-12 lg:px-12 ${
          isChatRoute ? "flex flex-1 min-h-0 overflow-hidden" : "flex-1"
        }`}
      >
        {children}
      </main>
      {/* <Suspense fallback={null}>
        <DemoBanner />
      </Suspense> */}
    </div>
  );
}
