"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type EmotionChartProps = {
  timeline: Array<{ date: string; sentiment_score: number; dominant_emotion: string }>;
  radar: Array<{ emotion: string; score: number }>;
};

export function EmotionChart({ timeline, radar }: EmotionChartProps) {
  const series = timeline.map((point) => ({
    ...point,
    positive_score: point.sentiment_score > 0 ? point.sentiment_score : null,
    negative_score: point.sentiment_score < 0 ? point.sentiment_score : null,
  }));

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="surface-card surface-card-hover rounded-2xl p-6">
        <div className="mb-4">
          <h3 className="text-base font-semibold text-mindmirror-primary">Sentiment Timeline</h3>
          <p className="text-sm text-mindmirror-secondary">Thirty-day emotional trend, color mapped by sentiment direction.</p>
        </div>
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis
                dataKey="date"
                tick={{ fill: "#9E9CB8", fontSize: 12 }}
                tickFormatter={(value) => String(value).slice(5)}
                axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
                tickLine={{ stroke: "rgba(255,255,255,0.08)" }}
              />
              <YAxis
                tick={{ fill: "#9E9CB8", fontSize: 12 }}
                domain={[-1, 1]}
                axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
                tickLine={{ stroke: "rgba(255,255,255,0.08)" }}
              />
              <Tooltip
                contentStyle={{
                  background: "#1A1730",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "#F5F3FF",
                  borderRadius: "16px",
                }}
                formatter={(value: unknown) => [Number(value).toFixed(2), "Sentiment"]}
              />
              <Legend wrapperStyle={{ color: "#9E9CB8" }} />
              <Line type="monotone" dataKey="positive_score" stroke="#A855F7" strokeWidth={3} dot={false} connectNulls />
              <Line type="monotone" dataKey="negative_score" stroke="#EC4899" strokeWidth={3} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="surface-card surface-card-hover rounded-2xl p-6">
        <div className="mb-4">
          <h3 className="text-base font-semibold text-mindmirror-primary">Weekly Emotion Radar</h3>
          <p className="text-sm text-mindmirror-secondary">Averaged emotional profile for the most recent week.</p>
        </div>
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radar}>
              <PolarGrid stroke="rgba(255,255,255,0.12)" />
              <PolarAngleAxis dataKey="emotion" tick={{ fill: "#9E9CB8", fontSize: 12 }} />
              <Radar
                name="Emotion"
                dataKey="score"
                stroke="#EC4899"
                fill="#EC4899"
                fillOpacity={0.28}
                strokeWidth={2}
              />
              <Tooltip
                contentStyle={{
                  background: "#1A1730",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "#F5F3FF",
                  borderRadius: "16px",
                }}
                formatter={(value: unknown) => [Number(value).toFixed(2), "Score"]}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
