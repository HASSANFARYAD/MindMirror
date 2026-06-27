"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { verifyEmail } from "@/lib/api";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in the URL.");
      return;
    }

    verifyEmail(token)
      .then((res) => {
        setStatus("success");
        setMessage(res.detail);
      })
      .catch((err: Error) => {
        setStatus("error");
        setMessage(err.message || "Verification failed. The link may have expired.");
      });
  }, [searchParams]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 text-center backdrop-blur-xl">
        {status === "verifying" && (
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-purple-400" />
        )}
        {status === "success" && (
          <CheckCircle className="mx-auto h-12 w-12 text-emerald-400" />
        )}
        {status === "error" && (
          <XCircle className="mx-auto h-12 w-12 text-red-400" />
        )}
        <h1 className="mt-4 text-xl font-semibold text-white">
          {status === "success"
            ? "Email Verified!"
            : status === "error"
              ? "Verification Failed"
              : "Verifying..."}
        </h1>
        <p className="mt-2 text-sm text-slate-400">{message}</p>
        {status === "success" && (
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-6 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 px-6 py-2.5 font-medium text-white transition-opacity hover:opacity-90"
          >
            Go to Dashboard
          </button>
        )}
        {status === "error" && (
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-6 rounded-xl bg-slate-700 px-6 py-2.5 font-medium text-white transition-colors hover:bg-slate-600"
          >
            Back to Dashboard
          </button>
        )}
      </div>
    </div>
  );
}
