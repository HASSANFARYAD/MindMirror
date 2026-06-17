export function emotionLabelFromScore(score: number): string {
  if (score > 0.35) return "uplifted";
  if (score > 0.1) return "steady";
  if (score < -0.35) return "heavy";
  if (score < -0.1) return "uneasy";
  return "balanced";
}

export function moodLabelFromText(text: string): string {
  const lowered = text.toLowerCase();

  if (/(happy|good|great|grateful|relieved|calm|hopeful|proud)/.test(lowered)) return emotionLabelFromScore(0.45);
  if (/(anxious|worried|nervous|panic|stressed|overwhelmed)/.test(lowered)) return emotionLabelFromScore(-0.25);
  if (/(sad|down|heavy|lonely|hurt|upset|gloomy)/.test(lowered)) return emotionLabelFromScore(-0.5);

  return emotionLabelFromScore(0);
}

export function normalizeEmotionScores(emotions: Record<string, number>): Array<{ emotion: string; score: number }> {
  return Object.entries(emotions)
    .sort((a, b) => b[1] - a[1])
    .map(([emotion, score]) => ({ emotion, score }));
}

export function wordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}
