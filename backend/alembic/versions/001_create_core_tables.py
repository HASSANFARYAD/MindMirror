"""Initial schema — create all core tables.

Revision ID: 001_create_core_tables
Revises:
Create Date: 2026-06-27 15:15:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "001_create_core_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          email TEXT UNIQUE NOT NULL,
          name TEXT,
          password_hash TEXT,
          email_verified BOOLEAN DEFAULT FALSE,
          verification_token TEXT,
          verification_token_expires_at TIMESTAMP,
          created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    op.execute("""
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
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_threads (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id),
          journal_entry_id UUID REFERENCES journal_entries(id),
          title TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id),
          thread_id UUID REFERENCES chat_threads(id) ON DELETE CASCADE,
          role TEXT CHECK (role IN ('user', 'assistant')),
          content TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS emotional_patterns (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id),
          pattern_type TEXT,
          description TEXT,
          detected_at TIMESTAMP DEFAULT NOW(),
          severity TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS weekly_insights (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id),
          week_start DATE,
          dominant_emotion TEXT,
          avg_sentiment FLOAT,
          top_triggers JSONB,
          cbt_recommendation TEXT,
          generated_at TIMESTAMP DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS weekly_insights")
    op.execute("DROP TABLE IF EXISTS emotional_patterns")
    op.execute("DROP TABLE IF EXISTS chat_messages")
    op.execute("DROP TABLE IF EXISTS chat_threads")
    op.execute("DROP TABLE IF EXISTS journal_entries")
    op.execute("DROP TABLE IF EXISTS users")
