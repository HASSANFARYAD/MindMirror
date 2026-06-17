"use client";

import { ArrowRight, Brain, Flame, Sparkles } from "lucide-react";
import clsx from "clsx";

type InsightCardProps = {
  title: string;
  description: string;
  badge?: string;
  severity?: "low" | "medium" | "high";
  icon?: "brain" | "sparkles" | "flame";
};

const icons = {
  brain: Brain,
  sparkles: Sparkles,
  flame: Flame,
};

export function InsightCard({ title, description, badge, severity = "low", icon = "sparkles" }: InsightCardProps) {
  const Icon = icons[icon];
  return (
    <article className="surface-card surface-card-hover rounded-2xl p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(139,92,246,0.15)] text-mindmirror-lavender">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-mindmirror-primary">{title}</h3>
            {badge ? (
              <span
                className={clsx(
                  "mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
                  severity === "high" && "bg-[rgba(236,72,153,0.15)] text-[#F9A8D4]",
                  severity === "medium" && "bg-[rgba(124,58,237,0.15)] text-[#C4B5FD]",
                  severity === "low" && "bg-[rgba(139,92,246,0.15)] text-[#DDD6FE]",
                )}
              >
                {badge}
              </span>
            ) : null}
          </div>
        </div>
        <ArrowRight className="h-4 w-4 text-mindmirror-muted" />
      </div>
      <p className="text-sm leading-6 text-mindmirror-secondary">{description}</p>
    </article>
  );
}
