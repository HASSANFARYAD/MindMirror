"use client";

import { useMemo } from "react";
import clsx from "clsx";

type MoodCalendarProps = {
  timeline: Array<{ date: string; sentiment_score: number; snippet?: string | null }>;
  onSelectDay?: (date: string, snippet?: string | null) => void;
};

export function MoodCalendar({ timeline, onSelectDay }: MoodCalendarProps) {
  const grid = useMemo(() => {
    const byDate = new Map(timeline.map((item) => [item.date.slice(0, 10), item]));
    const cells: Array<{ date: string; score: number; snippet?: string | null }> = [];
    const start = new Date();
    start.setDate(start.getDate() - 29);
    for (let i = 0; i < 30; i += 1) {
      const current = new Date(start);
      current.setDate(start.getDate() + i);
      const iso = current.toLocaleDateString("en-CA");
      const entry = byDate.get(iso);
      cells.push({ date: iso, score: entry?.sentiment_score ?? 0, snippet: entry?.snippet });
    }
    return cells;
  }, [timeline]);

  return (
    <section className="surface-card surface-card-hover rounded-2xl p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-mindmirror-primary">Mood Calendar</h3>
        <p className="text-sm text-mindmirror-secondary">Tap any day to inspect a journal snippet.</p>
      </div>
      <div className="grid grid-cols-5 gap-2 sm:grid-cols-6 lg:grid-cols-10">
        {grid.map((item) => (
          <button
            key={item.date}
            type="button"
            onClick={() => onSelectDay?.(item.date, item.snippet)}
            className={clsx(
              "group flex aspect-square items-center justify-center rounded-2xl border border-[rgba(255,255,255,0.08)] text-[11px] font-medium transition duration-200 ease-out hover:-translate-y-0.5",
              item.score > 0.35 && "bg-[rgba(16,185,129,0.22)] text-mindmirror-primary",
              item.score > 0.1 && item.score <= 0.35 && "bg-[rgba(16,185,129,0.14)] text-[#EDE9FE]",
              item.score <= 0.1 && item.score >= -0.1 && "bg-[rgba(255,255,255,0.04)] text-[#CFC9E3]",
              item.score < -0.1 && item.score >= -0.35 && "bg-[rgba(236,72,153,0.14)] text-[#FBCFE8]",
              item.score < -0.35 && "bg-[rgba(236,72,153,0.22)] text-mindmirror-primary",
            )}
          >
            <span className="opacity-80 group-hover:opacity-100">{item.date.slice(5, 10)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
