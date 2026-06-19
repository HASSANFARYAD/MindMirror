"use client";

import { useMemo, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { getTherapistExport, type TherapistExportSummary } from "@/lib/api";

const rangeOptions = [
  { label: "Last 7 days", value: "7" as const },
  { label: "Last 30 days", value: "30" as const },
  { label: "All time", value: "all" as const },
];

function ExportContent() {
  const [selectedRange, setSelectedRange] = useState<"7" | "30" | "all">("30");
  const [report, setReport] = useState<TherapistExportSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const subtitle = useMemo(
    () => "Export your emotional insights as a private PDF summary",
    [],
  );

  async function handleGenerate() {
    setLoading(true);
    setError(null);

    try {
      const nextReport = await getTherapistExport(selectedRange);
      setReport(nextReport);
      await new Promise<void>((resolve) => {
        window.requestAnimationFrame(() => resolve());
      });
      window.print();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to generate report.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell space-y-8">
      <div className="space-y-3">
        <h1 className="text-[48px] font-bold leading-[1.05] tracking-tight text-mindmirror-primary">
          <span className="gradient-title single-arc">Share with Your Therapist</span>
        </h1>
        <p className="max-w-2xl text-base leading-7 text-mindmirror-secondary">{subtitle}</p>
      </div>

      <section className="surface-card surface-card-hover print-hide rounded-2xl p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-mindmirror-primary">Date range</p>
            <p className="mt-1 text-sm text-mindmirror-secondary">Choose the window you want to share.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {rangeOptions.map((option) => {
              const active = option.value === selectedRange;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedRange(option.value)}
                  className={`rounded-full px-4 py-2 text-sm transition duration-200 ease-out ${
                    active
                      ? "bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] text-mindmirror-primary"
                      : "border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.04)] text-mindmirror-secondary hover:border-[rgba(255,255,255,0.24)] hover:text-mindmirror-primary"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => void handleGenerate()}
              disabled={loading}
              className="rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-5 py-2 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Generating..." : "Generate Report"}
            </button>
          </div>
        </div>
        {error ? <p className="mt-4 text-sm text-[#FCA5A5]">{error}</p> : null}
      </section>

      <section className="print-export-card surface-card surface-card-hover rounded-3xl p-8">
        <div className="flex items-start justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#7C3AED_0%,#EC4899_100%)] text-base font-bold text-mindmirror-primary">
              MM
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-mindmirror-primary">Therapist Export</h2>
              <p className="text-sm text-mindmirror-secondary">Private summary for professional sharing.</p>
            </div>
          </div>
          <div className="text-right text-sm text-mindmirror-secondary">
            <p>{report?.range_label ?? "No report generated yet"}</p>
            <p>{report?.generated_at ? `Generated ${new Date(report.generated_at).toLocaleString()}` : ""}</p>
          </div>
        </div>

        {report ? (
          <div className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-6">
              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Date range covered</p>
                <p className="mt-2 text-base text-mindmirror-primary">
                  {report.date_range_covered.start || "N/A"} to {report.date_range_covered.end || "N/A"}
                </p>
                <p className="mt-2 text-sm text-mindmirror-secondary">
                  Total journal entries analyzed: {report.total_journal_entries_analyzed}
                </p>
              </section>

              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Therapist summary</p>
                <p className="mt-3 text-sm leading-7 text-mindmirror-secondary">{report.therapist_summary}</p>
              </section>

              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Weekly insights text</p>
                <p className="mt-3 text-sm leading-7 text-mindmirror-secondary">{report.weekly_insights_text}</p>
              </section>
            </div>

            <div className="space-y-4">
              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Average sentiment</p>
                <p className="mt-3 text-4xl font-extrabold leading-none text-mindmirror-primary">
                  {report.average_sentiment_score.toFixed(2)}
                </p>
              </section>

              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Dominant emotions</p>
                <div className="mt-3 space-y-2">
                  {report.dominant_emotions.length ? (
                    report.dominant_emotions.map((item) => (
                      <div key={item.emotion} className="flex items-center justify-between text-sm">
                        <span className="capitalize text-mindmirror-primary">{item.emotion}</span>
                        <span className="text-mindmirror-secondary">{item.count}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-mindmirror-secondary">No emotions detected yet.</p>
                  )}
                </div>
              </section>

              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Cognitive distortions</p>
                <div className="mt-3 space-y-2">
                  {report.cognitive_distortions.length ? (
                    report.cognitive_distortions.map((item) => (
                      <div key={item.type} className="flex items-center justify-between text-sm">
                        <span className="capitalize text-mindmirror-primary">{item.type.replace(/_/g, " ")}</span>
                        <span className="text-mindmirror-secondary">{item.count}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-mindmirror-secondary">No distortions detected in this range.</p>
                  )}
                </div>
              </section>

              <section className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-5">
                <p className="text-xs uppercase tracking-[0.2em] text-[#8888AA]">Growth moments</p>
                <div className="mt-3 space-y-2">
                  {report.growth_moments_identified.length ? (
                    report.growth_moments_identified.map((item) => (
                      <p key={item} className="text-sm leading-6 text-mindmirror-secondary">
                        {item}
                      </p>
                    ))
                  ) : (
                    <p className="text-sm text-mindmirror-secondary">No growth moments identified yet.</p>
                  )}
                </div>
              </section>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border border-dashed border-[rgba(255,255,255,0.12)] p-8 text-sm text-mindmirror-secondary">
            Generate a report to populate this printable summary. Then use your browser&apos;s print dialog to save it as a PDF.
          </div>
        )}

        <div className="mt-8 border-t border-[rgba(255,255,255,0.08)] pt-5 text-sm text-mindmirror-secondary">
          <p className="font-medium text-mindmirror-primary">Confidential - For Therapist Use Only</p>
          <p className="mt-2">This summary is informational only and is not a medical device or a substitute for professional care.</p>
        </div>
      </section>
    </div>
  );
}

export default function ExportPage() {
  return (
    <AuthGate>
      <ExportContent />
    </AuthGate>
  );
}
