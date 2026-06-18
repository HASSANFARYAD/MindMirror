"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { signOutSession } from "@/lib/auth";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    signOutSession();
    router.replace("/login");
    router.refresh();
  }, [router]);

  return (
    <main className="page-shell flex min-h-[60vh] items-center justify-center px-5 py-16 text-center md:px-12">
      <div className="max-w-md rounded-[28px] border border-white/10 bg-white/5 px-8 py-10 text-sm text-mindmirror-secondary backdrop-blur-xl">
        Signing you out...
      </div>
    </main>
  );
}
