import { BrainCircuit, MessageSquareHeart, NotebookPen } from "lucide-react";
import { HomeActions } from "@/components/HomeActions";

const features = [
  {
    title: "Journal",
    description: "Capture what happened, what you felt, and what you're telling yourself in the moment.",
    icon: NotebookPen,
  },
  {
    title: "Understand",
    description: "Detect recurring emotional patterns, cognitive distortions, and trigger cycles over time.",
    icon: BrainCircuit,
  },
  {
    title: "Grow",
    description: "Get CBT-grounded reflections that turn insight into one small step you can actually take.",
    icon: MessageSquareHeart,
  },
] as const;

export default function HomePage() {
  return (
    <div className="relative py-8 md:py-12">
      <section className="page-shell relative grid gap-8 md:grid-cols-2 md:items-center">
        <div className="relative space-y-8">
          <div
            className="fade-in-up inline-flex rounded-lg border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.06)] px-4 py-2 text-sm font-medium text-mindmirror-primary"
            style={{ animationDelay: "0ms" }}
          >
            JWT-backed auth with private journaling
          </div>

          <div className="fade-in-up" style={{ animationDelay: "100ms" }}>
            <h1 className="max-w-3xl text-[48px] font-bold leading-[1.05] tracking-tight text-mindmirror-primary">
              <span className="gradient-title single-arc">Your mind deserves to be heard</span>
            </h1>
          </div>

          <p
            className="fade-in-up max-w-[480px] text-base leading-[1.7] text-mindmirror-secondary"
            style={{ animationDelay: "200ms" }}
          >
            MindMirror helps you journal, notice patterns, and talk through hard moments with a calm AI companion
            designed around Cognitive Behavioral Therapy.
          </p>

          <div className="fade-in-up" style={{ animationDelay: "300ms" }}>
            <HomeActions />
          </div>
        </div>

        <div className="relative min-h-[420px] md:min-h-[520px]">
          <div className="hero-orb left-12 top-10" />

          <div className="relative grid h-full gap-4 md:grid-cols-2">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className="fade-in-up surface-card surface-card-hover rounded-2xl p-6"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(139,92,246,0.15)] text-mindmirror-lavender">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h2 className="mt-3 text-base font-semibold text-mindmirror-primary">{feature.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-mindmirror-secondary">{feature.description}</p>
                </article>
              );
            })}

            <div className="fade-in-up surface-card surface-card-hover rounded-2xl p-6 md:col-span-2" style={{ animationDelay: "300ms" }}>
              <div className="flex items-center justify-between gap-4">
                <span className="text-sm font-medium text-mindmirror-secondary">Today&apos;s emotional check-in</span>
                <span className="rounded-full bg-[rgba(139,92,246,0.15)] px-3 py-1 text-[11px] font-medium text-[#C4B5FD]">
                  Calm support
                </span>
              </div>

              <div className="mt-5 space-y-4 rounded-2xl bg-[rgba(255,255,255,0.03)] p-4">
                <div className="h-1 w-full rounded-full bg-[linear-gradient(90deg,#7C3AED_0%,#EC4899_100%)] shadow-[0_0_8px_rgba(236,72,153,0.5)]" />
                <div className="space-y-2 text-sm leading-8 text-[#C4B5FD]">
                  <p>Notice the thought. Validate the feeling.</p>
                  <p>Reframe the story, then take one small step forward.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
