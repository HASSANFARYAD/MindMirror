import { Suspense } from "react";
import { AuthForm } from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="text-sm text-white/55">Loading signup...</div>}>
      <AuthForm mode="signup" />
    </Suspense>
  );
}
