"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGate } from "@/components/AuthGate";
import { JournalInput } from "@/components/JournalInput";
import { submitJournalEntry, transcribeVoice, type JournalAnalysis } from "@/lib/api";

function JournalContent() {
  const router = useRouter();
  const [content, setContent] = useState("");
  const [analysis, setAnalysis] = useState<JournalAnalysis | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [journalId, setJournalId] = useState<string | null>(null);
  const [voicePreview, setVoicePreview] = useState<string | null>(null);

  async function handleVoiceCaptured(voiceBlob: Blob) {
    setError(null);
    setIsTranscribing(true);
    try {
      const transcript = await transcribeVoice(voiceBlob);
      setVoicePreview(transcript.trim() || "No speech was detected in this recording.");
    } catch (caught) {
      setVoicePreview(null);
      setError(caught instanceof Error ? caught.message : "Failed to transcribe voice note.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function handleSubmit() {
    setIsSubmitting(true);
    setError(null);
    try {
      if (voicePreview) {
        throw new Error("Please insert or discard the voice transcript before submitting.");
      }
      const nextContent = content.trim();
      if (!nextContent) {
        throw new Error("Please type a reflection or record a voice note before submitting.");
      }
      const response = await submitJournalEntry({ content: nextContent, voice_file: null });
      setJournalId(response.id);
      setVoicePreview(null);
      setAnalysis({
        sentiment_score: response.sentiment_score ?? 0,
        sentiment_label: response.sentiment_label ?? "neutral",
        emotions: response.emotions ?? {},
        cognitive_distortions: response.cognitive_distortions ?? [],
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to submit reflection.");
    } finally {
      setIsSubmitting(false);
      setIsTranscribing(false);
    }
  }

  return (
    <div className="page-shell space-y-8">
      <div className="space-y-6">
        <div className="space-y-3">
          <h1 className="text-[48px] font-bold leading-[1.05] tracking-tight text-mindmirror-primary">
            <span className="gradient-title single-arc">Daily journal</span>
          </h1>
          <p className="max-w-2xl text-base leading-7 text-mindmirror-secondary">
            Write freely. MindMirror will highlight emotional patterns and CBT distortions gently, without judgment.
          </p>
        </div>
        <JournalInput
          value={content}
          onChange={setContent}
          onSubmit={handleSubmit}
          onVoiceCaptured={handleVoiceCaptured}
          onTranscribing={setIsTranscribing}
          analysis={analysis}
          isSubmitting={isSubmitting}
          validationError={error}
        />
        {voicePreview ? (
          <section className="surface-card surface-card-hover rounded-2xl p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-mindmirror-primary">Voice transcript preview</p>
                <p className="mt-1 text-xs text-mindmirror-secondary">Review this before you save the reflection.</p>
              </div>
              <button
                type="button"
                onClick={() => setVoicePreview(null)}
                className="rounded-full border border-[rgba(255,255,255,0.10)] bg-transparent px-3 py-2 text-xs text-mindmirror-secondary transition duration-200 ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
              >
                Discard
              </button>
            </div>
            <p className="mt-4 rounded-2xl bg-[rgba(255,255,255,0.03)] p-4 text-sm leading-6 text-mindmirror-primary">
              {voicePreview}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => {
                  const transcript = voicePreview.trim();
                  if (!transcript || transcript === "No speech was detected in this recording.") {
                    setVoicePreview(null);
                    return;
                  }
                  setContent((current) => {
                    const base = current.trim();
                    return base ? `${base}\n\n[Voice transcript]\n${transcript}` : `[Voice transcript]\n${transcript}`;
                  });
                  setVoicePreview(null);
                }}
                className="rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-4 py-2 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)]"
              >
                Insert into reflection
              </button>
              <button
                type="button"
                onClick={() => setVoicePreview(null)}
                className="rounded-full border border-[rgba(255,255,255,0.15)] bg-transparent px-4 py-2 text-sm text-mindmirror-secondary transition duration-[180ms] ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
              >
                Keep editing manually
              </button>
            </div>
          </section>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={!journalId}
            onClick={() => router.push(`/chat?entry=${encodeURIComponent(journalId ?? "")}`)}
            className="rounded-full bg-[linear-gradient(135deg,#EC4899_0%,#A855F7_100%)] px-5 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(236,72,153,0.35)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Talk to MindMirror about this
          </button>
          <button
            type="button"
            onClick={() => {
              setContent("");
              setAnalysis(null);
              setJournalId(null);
              setVoicePreview(null);
            }}
            className="rounded-full border border-[rgba(255,255,255,0.15)] bg-transparent px-5 py-3 text-sm font-medium text-mindmirror-secondary transition duration-[180ms] ease-out hover:border-[rgba(255,255,255,0.35)] hover:text-mindmirror-primary"
          >
            Clear entry
          </button>
        </div>
        {error ? <p className="text-sm text-[#FCA5A5]">{error}</p> : null}
        {isTranscribing ? <p className="text-sm text-mindmirror-secondary">Transcribing voice note...</p> : null}
      </div>
    </div>
  );
}

export default function JournalPage() {
  return (
    <AuthGate>
      <JournalContent />
    </AuthGate>
  );
}
