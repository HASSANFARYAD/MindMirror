CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Journal entries table
CREATE TABLE journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  content TEXT NOT NULL,
  voice_transcript TEXT,
  sentiment_score FLOAT,
  sentiment_label TEXT,
  emotions JSONB,
  cognitive_distortions JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Emotional patterns table
CREATE TABLE emotional_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  pattern_type TEXT,
  description TEXT,
  detected_at TIMESTAMP DEFAULT NOW(),
  severity TEXT
);

-- Weekly insights table
CREATE TABLE weekly_insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  week_start DATE,
  dominant_emotion TEXT,
  avg_sentiment FLOAT,
  top_triggers JSONB,
  cbt_recommendation TEXT,
  generated_at TIMESTAMP DEFAULT NOW()
);

