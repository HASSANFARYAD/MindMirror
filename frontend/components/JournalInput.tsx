"use client";

import { Mic, MicOff, Send } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { normalizeEmotionScores, wordCount } from "@/lib/sentiment";
import { previewEmotion, type EmotionPreview, type JournalAnalysis } from "@/lib/api";

type JournalInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => Promise<void> | void;
  onVoiceCaptured?: (voiceBlob: Blob) => Promise<void> | void;
  onTranscribing?: (isTranscribing: boolean) => void;
  analysis?: JournalAnalysis | null;
  isSubmitting?: boolean;
  placeholder?: string;
  validationError?: string | null;
};

const MAX_RECORDING_MS = 60_000;

export function JournalInput({
  value,
  onChange,
  onSubmit,
  onVoiceCaptured,
  onTranscribing,
  analysis = null,
  isSubmitting = false,
  placeholder = "What's on your mind today? Write freely...",
  validationError = null,
}: JournalInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<EmotionPreview | null>(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [animatedSentimentScore, setAnimatedSentimentScore] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const previewTimerRef = useRef<number | null>(null);
  const previewRequestRef = useRef(0);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
      if (previewTimerRef.current) {
        window.clearTimeout(previewTimerRef.current);
      }
      if (animationFrameRef.current) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const count = useMemo(() => wordCount(value), [value]);
  const emotionList = useMemo(() => (analysis ? normalizeEmotionScores(analysis.emotions) : []), [analysis]);
  const trimmedValue = useMemo(() => value.trim(), [value]);

  useEffect(() => {
    if (animationFrameRef.current) {
      window.cancelAnimationFrame(animationFrameRef.current);
    }

    if (!analysis) {
      setAnimatedSentimentScore(0);
      return;
    }

    const target = analysis.sentiment_score;
    const duration = 1200;
    const start = performance.now();

    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      setAnimatedSentimentScore(target * progress);
      if (progress < 1) {
        animationFrameRef.current = window.requestAnimationFrame(animate);
      }
    };

    animationFrameRef.current = window.requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [analysis?.sentiment_score]);

  useEffect(() => {
    if (previewTimerRef.current) {
      window.clearTimeout(previewTimerRef.current);
    }

    previewRequestRef.current += 1;
    const requestId = previewRequestRef.current;

    if (trimmedValue.length <= 50) {
      setPreviewResult(null);
      setPreviewVisible(false);
      return;
    }

    previewTimerRef.current = window.setTimeout(() => {
      void (async () => {
        try {
          const result = await previewEmotion(trimmedValue.slice(0, 500));
          if (previewRequestRef.current === requestId) {
            setPreviewResult(result);
            setPreviewVisible(false);
            window.requestAnimationFrame(() => setPreviewVisible(true));
          }
        } catch {
          if (previewRequestRef.current === requestId) {
            setPreviewResult(null);
            setPreviewVisible(false);
          }
        }
      })();
    }, 1200);

    return () => {
      if (previewTimerRef.current) {
        window.clearTimeout(previewTimerRef.current);
      }
    };
  }, [trimmedValue]);

  const previewEmoji = previewResult
    ? {
        joy: "😌",
        sadness: "😔",
        fear: "😰",
        anger: "🤬",
        neutral: "😶",
        surprise: "😯",
        disgust: "😣",
      }[previewResult.dominant_emotion] ?? "😶"
    : null;

  const sentimentColor =
    analysis && analysis.sentiment_score > 0.3
      ? "#43D9A2"
      : analysis && analysis.sentiment_score < -0.3
        ? "#FF6584"
        : "#FFB347";

  async function toggleRecording() {
    if (isRecording) {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
      recorderRef.current?.stop();
      setIsRecording(false);
      return;
    }
    try {
      setRecordError(null);
      if (!("MediaRecorder" in window)) {
        setRecordError("Voice recording is not supported in this browser.");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        if (timerRef.current) {
          window.clearTimeout(timerRef.current);
        }
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        onTranscribing?.(true);
        try {
          await onVoiceCaptured?.(blob);
        } finally {
          onTranscribing?.(false);
        }
      };
      recorder.start();
      timerRef.current = window.setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
          setIsRecording(false);
          setRecordError("Recording stopped automatically after 60 seconds.");
        }
      }, MAX_RECORDING_MS);
      setIsRecording(true);
    } catch (error) {
      setRecordError(error instanceof Error ? error.message : "Microphone access failed.");
    }
  }

  return (
    <section className="surface-card surface-card-hover rounded-2xl p-6">
      <div className="mb-4 flex items-center justify-between text-sm text-mindmirror-secondary">
        <span>Daily reflection</span>
        <span>{count} words</span>
      </div>
      <div className="relative">
        <textarea
          id="journal-entry"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          aria-describedby="journal-entry-help journal-entry-error"
          aria-invalid={Boolean(validationError)}
          className="min-h-[280px] w-full resize-none rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] p-5 pb-14 pr-28 text-base leading-7 text-mindmirror-primary outline-none transition placeholder:text-mindmirror-muted focus:border-[rgba(124,58,237,0.6)]"
        />
        {previewResult && previewEmoji ? (
          <div
            className={`pointer-events-none absolute bottom-4 right-4 flex items-center gap-2 rounded-full border border-[rgba(255,255,255,0.08)] bg-[rgba(13,11,26,0.82)] px-3 py-2 shadow-[0_8px_24px_rgba(0,0,0,0.2)] transition-opacity duration-300 ${
              previewVisible ? "opacity-100" : "opacity-0"
            }`}
            aria-live="polite"
          >
            <span className="text-base">{previewEmoji}</span>
            <span className="text-[11px] capitalize tracking-wide text-[#8888AA]">{previewResult.dominant_emotion}</span>
          </div>
        ) : null}
      </div>
      <p id="journal-entry-help" className="mt-2 text-xs text-mindmirror-muted">
        Write freely, or record a voice note and insert the transcript when you&apos;re ready.
      </p>
      {validationError ? (
        <p id="journal-entry-error" className="mt-2 text-sm text-[#FCA5A5]" role="alert">
          {validationError}
        </p>
      ) : null}
      {recordError ? <p className="mt-3 text-sm text-rose-300">{recordError}</p> : null}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={toggleRecording}
          aria-pressed={isRecording}
          disabled={isSubmitting}
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full border border-[rgba(255,255,255,0.15)] bg-transparent px-4 py-3 text-sm font-medium text-mindmirror-primary transition duration-[180ms] ease-out hover:border-[rgba(255,255,255,0.35)]"
        >
          {isRecording ? <MicOff className="h-4 w-4 text-mindmirror-pink" /> : <Mic className="h-4 w-4 text-mindmirror-pink" />}
          {isRecording ? "Stop recording" : "Voice note"}
        </button>
        <button
          type="button"
          onClick={() => onSubmit()}
          disabled={isSubmitting}
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-5 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Send className="h-4 w-4" />
          {isSubmitting ? "Analyzing..." : "Submit reflection"}
        </button>
      </div>

      {analysis ? (
        <section className="surface-card surface-card-hover mt-6 rounded-2xl p-6">
          <h2 className="text-base font-semibold text-mindmirror-primary">Analysis result</h2>
          <p className="mt-2 text-sm text-mindmirror-secondary">Emotion summary and detected CBT patterns.</p>
          <div className="mt-5 space-y-4">
            <div className="rounded-2xl bg-[rgba(255,255,255,0.03)] p-4">
              <p className="text-[12px] tracking-wide text-[#8888AA]">Emotional Score</p>
              <p className="mt-2 text-[48px] font-extrabold leading-none" style={{ color: sentimentColor }}>
                {animatedSentimentScore.toFixed(2)}
              </p>
              <p className="mt-2 text-sm text-mindmirror-secondary">{analysis.sentiment_label}</p>
            </div>
            <div className="space-y-3">
              {emotionList.slice(0, 5).map((emotion) => (
                <div key={emotion.emotion} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize text-mindmirror-primary">{emotion.emotion}</span>
                    <span className="text-mindmirror-secondary">{emotion.score.toFixed(2)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[rgba(255,255,255,0.08)]">
                    <div
                      className="h-2 rounded-full bg-[linear-gradient(90deg,#7C3AED_0%,#EC4899_100%)]"
                      style={{ width: `${Math.max(emotion.score * 100, 5)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-mindmirror-primary">Detected distortions</p>
              {analysis.cognitive_distortions.length ? (
                analysis.cognitive_distortions.map((distortion) => (
                  <div key={`${distortion.type}-${distortion.evidence}`} className="rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-medium capitalize text-mindmirror-primary">{distortion.type}</p>
                      <span className="rounded-full bg-[rgba(124,58,237,0.15)] px-2.5 py-1 text-xs text-[#C4B5FD]">
                        {Math.round(distortion.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-mindmirror-secondary">{distortion.evidence}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-mindmirror-secondary">No strong distortion pattern detected.</p>
              )}
            </div>
          </div>
        </section>
      ) : null}
    </section>
  );
}
