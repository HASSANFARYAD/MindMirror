CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  password_hash TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Journal entries table
CREATE TABLE IF NOT EXISTS journal_entries (
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

-- Chat threads table
CREATE TABLE IF NOT EXISTS chat_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  journal_entry_id UUID REFERENCES journal_entries(id),
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  thread_id UUID REFERENCES chat_threads(id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Emotional patterns table
CREATE TABLE IF NOT EXISTS emotional_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  pattern_type TEXT,
  description TEXT,
  detected_at TIMESTAMP DEFAULT NOW(),
  severity TEXT
);

-- Weekly insights table
CREATE TABLE IF NOT EXISTS weekly_insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  week_start DATE,
  dominant_emotion TEXT,
  avg_sentiment FLOAT,
  top_triggers JSONB,
  cbt_recommendation TEXT,
  generated_at TIMESTAMP DEFAULT NOW()
);
