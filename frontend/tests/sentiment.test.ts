import { describe, it, expect } from 'vitest';
import {
  emotionLabelFromScore,
  moodLabelFromText,
  normalizeEmotionScores,
  wordCount,
} from '@/lib/sentiment';

describe('emotionLabelFromScore', () => {
  it('returns uplifted for scores > 0.35', () => {
    expect(emotionLabelFromScore(0.5)).toBe('uplifted');
    expect(emotionLabelFromScore(0.36)).toBe('uplifted');
  });

  it('returns steady for scores > 0.1 and <= 0.35', () => {
    expect(emotionLabelFromScore(0.35)).toBe('steady');
    expect(emotionLabelFromScore(0.2)).toBe('steady');
  });

  it('returns balanced for scores between -0.1 and 0.1 inclusive', () => {
    expect(emotionLabelFromScore(0.1)).toBe('balanced');
    expect(emotionLabelFromScore(0)).toBe('balanced');
    expect(emotionLabelFromScore(-0.1)).toBe('balanced');
    expect(emotionLabelFromScore(-0.05)).toBe('balanced');
  });

  it('returns uneasy for scores <= -0.1 and > -0.35', () => {
    expect(emotionLabelFromScore(-0.2)).toBe('uneasy');
    expect(emotionLabelFromScore(-0.35)).toBe('uneasy');
  });

  it('returns heavy for scores < -0.35', () => {
    expect(emotionLabelFromScore(-0.5)).toBe('heavy');
    expect(emotionLabelFromScore(-0.36)).toBe('heavy');
  });
});

describe('moodLabelFromText', () => {
  it('detects positive moods', () => {
    expect(moodLabelFromText('I feel happy today')).toBe('uplifted');
  });

  it('detects anxious moods', () => {
    expect(moodLabelFromText('I feel anxious about work')).toBe('uneasy');
  });

  it('detects sad moods', () => {
    expect(moodLabelFromText('I feel so sad and lonely')).toBe('heavy');
  });

  it('returns balanced for neutral text', () => {
    expect(moodLabelFromText('I went to the store')).toBe('balanced');
  });
});

describe('normalizeEmotionScores', () => {
  it('sorts by score descending', () => {
    const result = normalizeEmotionScores({ joy: 0.1, sadness: 0.8, anger: 0.3 });
    expect(result).toEqual([
      { emotion: 'sadness', score: 0.8 },
      { emotion: 'anger', score: 0.3 },
      { emotion: 'joy', score: 0.1 },
    ]);
  });

  it('returns empty array for empty input', () => {
    expect(normalizeEmotionScores({})).toEqual([]);
  });
});

describe('wordCount', () => {
  it('counts words in a sentence', () => {
    expect(wordCount('hello world')).toBe(2);
  });

  it('returns 0 for empty string', () => {
    expect(wordCount('')).toBe(0);
  });

  it('returns 0 for whitespace-only string', () => {
    expect(wordCount('   ')).toBe(0);
  });

  it('handles multiple spaces', () => {
    expect(wordCount('hello   world  test')).toBe(3);
  });
});
