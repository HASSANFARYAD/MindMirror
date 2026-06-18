"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, TrendingUp } from "lucide-react";
import { EmotionChart } from "@/components/EmotionChart";
import { InsightCard } from "@/components/InsightCard";
import { MoodCalendar } from "@/components/MoodCalendar";
import { AuthGate } from "@/components/AuthGate";
import { getEmotionalMap, type GrowthStory } from "@/lib/api";

function DashboardContent() {
  const [timeline, setTimeline] = useState<Array<{ date: string; sentiment_score: number; dominant_emotion: string; emotions: Record<string, number>; snippet?: string | null }>>([]);
  const [radar, setRadar] = useState<Array<{ emotion: string; score: number }>>([]);
  const [patterns, setPatterns] = useState<Array<{ pattern_type: string; description: string; severity: string }>>([]);
  const [insights, setInsights] = useState<Array<{ dominant_emotion?: string | null; avg_sentiment?: number | null; top_triggers?: Array<{ term: string; count: number }> | null; cbt_recommendation?: string | null }>>([]);
  const [growthStory, setGrowthStory] = useState<GrowthStory | null>(null);
  const [selectedSnippet, setSelectedSnippet] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [celebrationVisible, setCelebrationVisible] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setLoadError(null);
        const data = await getEmotionalMap();
        setTimeline(data.timeline);
        setRadar(data.radar);
        setPatterns(data.patterns);
        setInsights(data.weekly_insights);
        setGrowthStory(data.growth_story ?? null);
      } catch {
        setLoadError("We could not load your dashboard right now. Please try again in a moment.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  useEffect(() => {
    if (!growthStory?.show || growthStory.now.distortion_avg !== 0) {
      return;
    }

    setCelebrationVisible(true);
    if (window.sessionStorage.getItem("confetti_shown") === "true") {
      return;
    }

    window.sessionStorage.setItem("confetti_shown", "true");
    void import("canvas-confetti").then(({ default: confetti }) => {
      confetti({
        particleCount: 80,
        spread: 60,
        colors: ["#6C63FF", "#FF6584", "#43D9A2"],
        origin: { y: 0.4 },
      });
    });
  }, [growthStory]);

  const selectedInsight = useMemo(() => insights[0], [insights]);
  const hasData = timeline.length > 0 || radar.length > 0 || patterns.length > 0 || insights.length > 0;

  return (
    <div className="page-shell space-y-8">
      <div className="space-y-3">
        <h1 className="text-[48px] font-bold leading-[1.05] tracking-tight text-mindmirror-primary">
          <span className="gradient-title single-arc">Emotional map</span>
        </h1>
        <p className="max-w-2xl text-base leading-7 text-mindmirror-secondary">
          A 30-day view of your sentiment, recurring patterns, and weekly CBT guidance.
        </p>
      </div>

      {loading ? (
        <div className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-2">
            <div className="h-[320px] animate-pulse rounded-2xl bg-gray-800" />
            <div className="h-[320px] animate-pulse rounded-2xl bg-gray-800" />
          </div>
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="h-[360px] animate-pulse rounded-2xl bg-gray-800" />
            <div className="space-y-4">
              <div className="h-40 animate-pulse rounded-2xl bg-gray-800" />
              <div className="h-40 animate-pulse rounded-2xl bg-gray-800" />
            </div>
          </div>
        </div>
      ) : loadError ? (
        <section className="surface-card surface-card-hover rounded-2xl p-8 text-center">
          <div className="mx-auto max-w-xl space-y-3">
            <h2 className="text-2xl font-semibold text-mindmirror-primary">Dashboard unavailable</h2>
            <p className="text-sm leading-6 text-mindmirror-secondary">{loadError}</p>
          </div>
        </section>
      ) : hasData ? (
        <>
          <EmotionChart timeline={timeline} radar={radar} />

          {growthStory?.show ? (
            <section className="rounded-2xl border border-[rgba(67,217,162,0.3)] bg-[linear-gradient(135deg,rgba(108,99,255,0.15),rgba(67,217,162,0.15))] p-8">
              <div className="mb-6 flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-2xl font-semibold text-mindmirror-primary">Your Growth Story</h3>
                  <p className="mt-2 text-sm text-mindmirror-secondary">
                    A before-and-after view of how your emotional patterns have changed.
                  </p>
                </div>
                <div className="rounded-full border border-[rgba(255,255,255,0.14)] bg-[rgba(255,255,255,0.08)] px-3 py-1 text-xs text-mindmirror-secondary">
                  Oldest 5 vs newest 5
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] lg:items-stretch">
                <div className="rounded-2xl bg-[rgba(255,255,255,0.06)] p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-[#B4B0E0]">When you started</p>
                  <div className="mt-4 space-y-4">
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Average sentiment</p>
                      <span
                        className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                          growthStory.started.avg_sentiment > 0.3
                            ? "bg-[rgba(67,217,162,0.18)] text-[#B7F7E4]"
                            : growthStory.started.avg_sentiment < -0.3
                              ? "bg-[rgba(255,101,132,0.18)] text-[#FFC0CF]"
                              : "bg-[rgba(255,179,71,0.18)] text-[#FFE3B2]"
                        }`}
                      >
                        {growthStory.started.avg_sentiment.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Most frequent emotion</p>
                      <span className="mt-2 inline-flex rounded-full bg-[rgba(108,99,255,0.18)] px-3 py-1 text-sm font-medium capitalize text-[#DDD6FE]">
                        {growthStory.started.dominant_emotion}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Cognitive distortions per entry</p>
                      <p className="mt-2 text-2xl font-bold text-mindmirror-primary">
                        {growthStory.started.distortion_avg.toFixed(1)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex min-h-[220px] flex-col items-center justify-center rounded-2xl border border-dashed border-[rgba(255,255,255,0.16)] bg-[rgba(255,255,255,0.04)] px-8 py-6 text-center">
                  <div className="text-5xl leading-none text-[#B7F7E4] animate-pulse">→</div>
                  <p className="mt-3 text-sm font-medium uppercase tracking-[0.2em] text-[#B4B0E0]">Your Journey</p>
                </div>

                <div className="rounded-2xl bg-[rgba(255,255,255,0.06)] p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-[#B4B0E0]">Where you are now</p>
                  <div className="mt-4 space-y-4">
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Average sentiment</p>
                      <span
                        className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                          growthStory.now.avg_sentiment > 0.3
                            ? "bg-[rgba(67,217,162,0.18)] text-[#B7F7E4]"
                            : growthStory.now.avg_sentiment < -0.3
                              ? "bg-[rgba(255,101,132,0.18)] text-[#FFC0CF]"
                              : "bg-[rgba(255,179,71,0.18)] text-[#FFE3B2]"
                        }`}
                      >
                        {growthStory.now.avg_sentiment.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Most frequent emotion</p>
                      <span className="mt-2 inline-flex rounded-full bg-[rgba(67,217,162,0.16)] px-3 py-1 text-sm font-medium capitalize text-[#B7F7E4]">
                        {growthStory.now.dominant_emotion}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-mindmirror-secondary">Cognitive distortions per entry</p>
                      <p className="mt-2 text-2xl font-bold text-mindmirror-primary">
                        {growthStory.now.distortion_avg.toFixed(1)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <p className="mt-6 rounded-2xl bg-[rgba(13,11,26,0.35)] px-5 py-4 text-sm leading-7 text-mindmirror-primary">
                {growthStory.summary}
              </p>

              {celebrationVisible && growthStory.now.distortion_avg === 0 ? (
                <p className="mt-4 text-center text-sm font-medium text-[#43D9A2]">
                  🎉 You&apos;ve eliminated cognitive distortions from your recent entries!
                </p>
              ) : null}
            </section>
          ) : null}

          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <MoodCalendar timeline={timeline} onSelectDay={(_, snippet) => setSelectedSnippet(snippet ?? null)} />

            <section className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <InsightCard
                  title="Trigger patterns"
                  description={
                    patterns.find((pattern) => pattern.pattern_type === "trigger")?.description ??
                    "No clear trigger loop detected yet."
                  }
                  severity={
                    patterns.find((pattern) => pattern.pattern_type === "trigger")?.severity as
                      | "low"
                      | "medium"
                      | "high"
                      | undefined
                  }
                  badge="Recurring"
                  icon="flame"
                />
                <InsightCard
                  title="Emotional cycles"
                  description={
                    patterns.find((pattern) => pattern.pattern_type === "cycle")?.description ??
                    "No stable weekly cycle identified."
                  }
                  severity={
                    patterns.find((pattern) => pattern.pattern_type === "cycle")?.severity as
                      | "low"
                      | "medium"
                      | "high"
                      | undefined
                  }
                  badge="Week pattern"
                  icon="sparkles"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <InsightCard
                  title="Growth moments"
                  description={
                    patterns.find((pattern) => pattern.pattern_type === "growth")?.description ??
                    "Sustained improvement will appear here after several positive days."
                  }
                  severity={
                    patterns.find((pattern) => pattern.pattern_type === "growth")?.severity as
                      | "low"
                      | "medium"
                      | "high"
                      | undefined
                  }
                  badge="Momentum"
                  icon="sparkles"
                />
                <InsightCard
                  title="Gentle alert"
                  description={
                    patterns.find((pattern) => pattern.pattern_type === "alert")?.description ??
                    "No alert condition detected."
                  }
                  severity={
                    patterns.find((pattern) => pattern.pattern_type === "alert")?.severity as
                      | "low"
                      | "medium"
                      | "high"
                      | undefined
                  }
                  badge="Support"
                  icon="flame"
                />
              </div>

              <section className="surface-card surface-card-hover rounded-2xl p-6">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-2xl bg-[rgba(139,92,246,0.15)] p-3 text-mindmirror-lavender">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-mindmirror-primary">CBT insight of the week</h3>
                    <p className="text-sm text-mindmirror-secondary">A concise reflection based on the latest journal trends.</p>
                  </div>
                </div>
                {selectedInsight ? (
                  <div className="space-y-4 text-sm text-mindmirror-secondary">
                    <p>
                      Dominant emotion: <span className="text-mindmirror-primary">{selectedInsight.dominant_emotion ?? "neutral"}</span>
                    </p>
                    <p>
                      Average sentiment: <span className="text-mindmirror-primary">{selectedInsight.avg_sentiment?.toFixed(2) ?? "0.00"}</span>
                    </p>
                    <p>
                      Top triggers:{" "}
                      <span className="text-mindmirror-primary">
                        {(selectedInsight.top_triggers ?? []).map((trigger) => trigger.term).join(", ") || "none yet"}
                      </span>
                    </p>
                    <div className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-4">
                      <p className="font-medium text-mindmirror-primary">Practice this:</p>
                      <p className="mt-2">{selectedInsight.cbt_recommendation}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-mindmirror-secondary">Your weekly insight will appear here.</p>
                )}
              </section>

              {selectedSnippet ? (
                <section className="surface-card surface-card-hover rounded-2xl p-6">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="rounded-2xl bg-[rgba(236,72,153,0.15)] p-3 text-mindmirror-pink">
                      <CalendarDays className="h-5 w-5" />
                    </div>
                    <h3 className="text-base font-semibold text-mindmirror-primary">Selected day</h3>
                  </div>
                  <p className="text-sm leading-6 text-mindmirror-secondary">{selectedSnippet}</p>
                </section>
              ) : null}
            </section>
          </div>
        </>
      ) : (
        <section className="surface-card surface-card-hover rounded-2xl p-8 text-center">
          <div className="mx-auto max-w-xl space-y-3">
            <h2 className="text-2xl font-semibold text-mindmirror-primary">Your dashboard is waiting for its first data</h2>
            <p className="text-sm leading-6 text-mindmirror-secondary">
              Start a journal entry and come back here to see your sentiment timeline, emotional radar, and recurring patterns.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGate>
      <DashboardContent />
    </AuthGate>
  );
}
