"use client";

import { Mic, MicOff, Send } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { wordCount } from "@/lib/sentiment";

type JournalInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => Promise<void> | void;
  onVoiceCaptured?: (voiceBlob: Blob) => Promise<void> | void;
  onTranscribing?: (isTranscribing: boolean) => void;
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
  isSubmitting = false,
  placeholder = "What's on your mind today? Write freely...",
  validationError = null,
}: JournalInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  const count = useMemo(() => wordCount(value), [value]);

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
      <textarea
        id="journal-entry"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-describedby="journal-entry-help journal-entry-error"
        aria-invalid={Boolean(validationError)}
        className="min-h-[280px] w-full resize-none rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] p-5 text-base leading-7 text-mindmirror-primary outline-none transition placeholder:text-mindmirror-muted focus:border-[rgba(124,58,237,0.6)]"
      />
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
    </section>
  );
}
