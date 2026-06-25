"use client";

import { useState } from "react";

const DISMISSED_KEY = "mindmirror_crisis_banner_dismissed";

export function CrisisBanner() {
  const [visible, setVisible] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.sessionStorage.getItem(DISMISSED_KEY) !== "true";
  });

  function handleDismiss() {
    setVisible(false);
    try {
      window.sessionStorage.setItem(DISMISSED_KEY, "true");
    } catch {
      // sessionStorage unavailable — no-op
    }
  }

  if (!visible) return null;

  return (
    <div
      className="relative z-40 border-b border-[rgba(255,179,71,0.25)] bg-[rgba(255,179,71,0.1)] backdrop-blur-[6px]"
      role="alert"
    >
      <div className="mx-auto flex max-w-[1280px] items-start justify-between gap-4 px-5 py-3 md:px-12">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm text-mindmirror-primary">
          <span className="font-medium">If you&apos;re in crisis:</span>
          <span>
            Call or text{" "}
            <a
              href="tel:988"
              className="font-semibold text-[#F9A8D4] underline decoration-[rgba(249,168,212,0.3)] underline-offset-2 transition hover:decoration-[rgba(249,168,212,0.8)]"
            >
              988
            </a>{" "}
            (US Suicide &amp; Crisis Lifeline) or{" "}
            <a
              href="tel:116123"
              className="font-semibold text-[#F9A8D4] underline decoration-[rgba(249,168,212,0.3)] underline-offset-2 transition hover:decoration-[rgba(249,168,212,0.8)]"
            >
              116 123
            </a>{" "}
            (UK/IE Samaritans).
          </span>
          <span className="text-mindmirror-secondary">
            MindMirror is not a crisis service — it does not replace professional care.
          </span>
        </div>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss crisis banner"
          className="shrink-0 rounded-full px-2.5 py-1 text-sm text-mindmirror-secondary transition hover:bg-[rgba(255,255,255,0.08)] hover:text-mindmirror-primary"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
