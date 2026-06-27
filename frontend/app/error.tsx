"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: Props) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-8">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 text-center backdrop-blur-xl">
        <AlertTriangle className="mx-auto h-12 w-12 text-amber-400" />
        <h1 className="mt-4 text-xl font-semibold text-white">Page Error</h1>
        <p className="mt-2 text-sm text-slate-400">
          {error.message || "Something went wrong loading this page."}
        </p>
        <button
          onClick={reset}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </button>
      </div>
    </div>
  );
}
