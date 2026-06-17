import { Suspense } from "react";
import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="text-sm text-white/55">Loading login...</div>}>
      <AuthForm mode="login" />
    </Suspense>
  );
}
