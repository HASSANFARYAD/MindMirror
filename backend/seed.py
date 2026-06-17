from __future__ import annotations

import asyncio
import json
import os
import random
import uuid
from datetime import date, datetime, timedelta

import asyncpg
from passlib.hash import bcrypt

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://mindmirror_user:mindmirror_pass@localhost:5432/mindmirror",
)

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_EMAIL = "demo@mindmirror.app"
DEMO_USER_NAME = "Alex"
DEMO_USER_PASSWORD = "Demo1234!"

RNG = random.Random(42)


def fixed_uuid(seed_value: int) -> uuid.UUID:
    """Create a deterministic UUID for idempotent seed rows."""
    return uuid.UUID(f"00000000-0000-0000-0000-{seed_value:012x}")


def start_of_day(target_date: date) -> datetime:
    return datetime(target_date.year, target_date.month, target_date.day)


def sentiment_label(score: float) -> str:
    if score >= 0.2:
        return "positive"
    if score <= -0.2:
        return "negative"
    return "neutral"


def random_emotions(bounds: dict[str, tuple[float, float]]) -> dict[str, float]:
    return {name: round(RNG.uniform(low, high), 3) for name, (low, high) in bounds.items()}


def sample_text(options: list[str]) -> str:
    return RNG.choice(options)


def phase_for_day(age_in_days: int) -> str:
    if age_in_days >= 20:
        return "phase_1"
    if age_in_days >= 10:
        return "phase_2"
    return "phase_3"


async def ensure_schema(conn: asyncpg.Connection) -> None:
    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")


async def seed_demo_user(conn: asyncpg.Connection) -> None:
    password_hash = bcrypt.hash(DEMO_USER_PASSWORD)
    await conn.execute(
        """
        INSERT INTO users (id, email, name, password_hash)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (email)
        DO UPDATE SET
            id = EXCLUDED.id,
            name = EXCLUDED.name,
            password_hash = EXCLUDED.password_hash
        """,
        DEMO_USER_ID,
        DEMO_USER_EMAIL,
        DEMO_USER_NAME,
        password_hash,
    )


async def seed_journal_entries(conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
    phase_1_texts = [
        "I can't seem to focus on anything today. Everything feels heavy.",
        "Had another bad night. I keep thinking I'm going to fail my exams.",
        "Nobody seems to understand what I'm going through. I feel so alone.",
        "I know I always mess things up. Today was no different.",
        "Everything feels pointless. I don't know why I even try.",
        "I'm so tired all the time. I feel like I'm falling behind everyone.",
        "Had a panic attack before my presentation. I'm so embarrassed.",
        "I should be doing better by now. Everyone else seems fine except me.",
        "Another day where I couldn't get out of bed until noon. I'm a mess.",
        "I feel worthless. Like nothing I do actually matters.",
    ]
    phase_2_texts = [
        "Talked to a friend today. It actually helped a little.",
        "Had a decent morning. Small win but I'll take it.",
        "Tried the box breathing technique. It calmed me down during a stressful moment.",
        "I'm starting to notice my thoughts are pretty harsh on myself.",
        "Went for a walk outside. First time in a while. Felt okay.",
        "I reframed a negative thought today - instead of 'I always fail' I said 'I'm still learning'.",
        "Journaling is helping me see patterns I didn't notice before.",
        "Had a hard conversation with my professor. It went better than I expected.",
        "I realize I've been catastrophizing a lot. Going to try to catch myself.",
        "Feeling a bit lighter today. Not sure why but I'll accept it.",
    ]
    phase_3_texts = [
        "Had a genuinely good day today. Finished my assignment and felt proud.",
        "I caught myself catastrophizing and stopped it. Real progress.",
        "Feeling grateful for small things. Coffee, sunlight, a good conversation.",
        "Slept well for the third night in a row. My energy is coming back.",
        "I'm starting to feel like myself again. It's been a while.",
        "Helped a classmate today. Felt good to give instead of just receive.",
        "I set a boundary today and it felt empowering not scary.",
        "Looking back at my early entries - I've come so far.",
        "Excited about a new project. Curiosity feels good.",
        "I feel hopeful. That's new. I'll hold onto it.",
    ]

    phase_1_emotion_bounds = {
        "sadness": (0.6, 0.8),
        "fear": (0.4, 0.6),
        "joy": (0.05, 0.15),
        "anger": (0.1, 0.3),
        "neutral": (0.1, 0.2),
        "surprise": (0.05, 0.1),
        "disgust": (0.1, 0.2),
    }
    phase_2_emotion_bounds = {
        "sadness": (0.2, 0.4),
        "fear": (0.1, 0.3),
        "joy": (0.2, 0.4),
        "anger": (0.05, 0.1),
        "neutral": (0.3, 0.5),
        "surprise": (0.1, 0.3),
        "disgust": (0.05, 0.1),
    }
    phase_3_emotion_bounds = {
        "sadness": (0.05, 0.15),
        "fear": (0.05, 0.1),
        "joy": (0.5, 0.8),
        "anger": (0.02, 0.05),
        "neutral": (0.2, 0.4),
        "surprise": (0.1, 0.2),
        "disgust": (0.02, 0.05),
    }
    distortion_pool = [
        "catastrophizing",
        "all_or_nothing",
        "emotional_reasoning",
        "should_statements",
        "overgeneralization",
    ]

    today = date.today()
    entries: list[dict[str, object]] = []
    for age_in_days in range(29, -1, -1):
        current_date = today - timedelta(days=age_in_days)
        phase = phase_for_day(age_in_days)
        if phase == "phase_1":
            content = sample_text(phase_1_texts)
            emotions = random_emotions(phase_1_emotion_bounds)
            sentiment_score = round(RNG.uniform(-0.7, -0.3), 3)
            distortion_count = RNG.randint(2, 3)
            distortions = RNG.sample(distortion_pool, distortion_count)
        elif phase == "phase_2":
            content = sample_text(phase_2_texts)
            emotions = random_emotions(phase_2_emotion_bounds)
            sentiment_score = round(RNG.uniform(-0.2, 0.3), 3)
            distortions = RNG.sample(distortion_pool, RNG.randint(0, 1))
        else:
            content = sample_text(phase_3_texts)
            emotions = random_emotions(phase_3_emotion_bounds)
            sentiment_score = round(RNG.uniform(0.3, 0.8), 3)
            distortions = []

        entries.append(
            {
                "id": fixed_uuid(1001 + age_in_days),
                "user_id": user_id,
                "content": content,
                "voice_transcript": None,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label(sentiment_score),
                "emotions": emotions,
                "cognitive_distortions": distortions,
                "created_at": start_of_day(current_date),
            }
        )

    query = """
        INSERT INTO journal_entries (
            id, user_id, content, voice_transcript, sentiment_score,
            sentiment_label, emotions, cognitive_distortions, created_at
        )
        VALUES (
            $1, $2, $3, $4, $5, $6,
            $7::jsonb, $8::jsonb, $9
        )
        ON CONFLICT (id) DO NOTHING
    """
    for entry in entries:
        await conn.execute(
            query,
            entry["id"],
            entry["user_id"],
            entry["content"],
            entry["voice_transcript"],
            entry["sentiment_score"],
            entry["sentiment_label"],
            json.dumps(entry["emotions"]),
            json.dumps(entry["cognitive_distortions"]),
            entry["created_at"],
        )


async def seed_chat_history(conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
    pairs = [
        (
            15,
            "I feel like no matter what I do it's never good enough.",
            "That sounds exhausting, carrying that weight every day. What you're describing sounds like a really painful pattern - where your mind sets an impossible standard and then criticizes you for not reaching it. That's called perfectionism, and it's more common than you think. Can I ask - whose voice does that sound like when you hear 'not good enough'? Is it yours, or someone else's from your past?",
        ),
        (
            12,
            "I tried the breathing exercise. It actually helped during my panic attack today.",
            "That's a genuinely big deal - using a tool in the middle of a panic attack takes real presence of mind. You should feel proud of that. How did it feel to get through it using something you learned? I'm curious what that moment was like for you on the other side of it.",
        ),
        (
            9,
            "I caught myself thinking 'I always fail' and changed it to 'I'm still learning'. Is that what reframing means?",
            "Yes - that's exactly what reframing means, and you did it perfectly. You noticed the distortion, paused, and chose a more accurate thought. That's the core of CBT in action. The fact that you caught it in real time, not just in reflection, shows real progress. What situation triggered that thought today?",
        ),
        (
            6,
            "I'm actually feeling better this week. Is that okay to say?",
            "Not only is it okay - it's wonderful to hear. Growth doesn't mean never struggling again, it means you have more tools when you do. How does it feel to notice this shift in yourself? Sometimes acknowledging progress is just as important as acknowledging pain.",
        ),
        (
            3,
            "I set a boundary with someone today. It was scary.",
            "Setting a boundary is one of the most self-respecting things a person can do, and it almost always feels scary the first few times. The fear doesn't mean you did something wrong - it usually means you did something new. How did the other person respond, and how are you feeling now that you did it?",
        ),
        (
            1,
            "Looking back at my first journal entries - I can't believe how far I've come.",
            "Reading that genuinely made me smile. The person who wrote those first entries was struggling - and they still showed up every day to reflect, to try, to be honest. That's not small. That's everything. What feels most different about how you see yourself now compared to then?",
        ),
    ]

    base_date = date.today()
    message_id = 2001
    for age_in_days, user_text, assistant_text in pairs:
        message_date = base_date - timedelta(days=age_in_days)
        user_created_at = datetime(message_date.year, message_date.month, message_date.day, 9, 0)
        assistant_created_at = datetime(message_date.year, message_date.month, message_date.day, 9, 2)

        await conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, created_at)
            VALUES ($1, $2, 'user', $3, $4)
            ON CONFLICT (id) DO NOTHING
            """,
            fixed_uuid(message_id),
            user_id,
            user_text,
            user_created_at,
        )
        message_id += 1

        await conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, created_at)
            VALUES ($1, $2, 'assistant', $3, $4)
            ON CONFLICT (id) DO NOTHING
            """,
            fixed_uuid(message_id),
            user_id,
            assistant_text,
            assistant_created_at,
        )
        message_id += 1


async def seed_patterns(conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
    today = date.today()
    patterns = [
        (
            "trigger",
            "Exam and academic pressure consistently precedes emotional lows. Words like 'fail', 'behind', and 'presentation' appear frequently before sentiment drops below -0.4.",
            "medium",
            today - timedelta(days=20),
        ),
        (
            "cycle",
            "Emotional scores show a gradual recovery arc over 30 days - from consistent lows in the -0.5 range to sustained positivity above 0.4. This suggests responsiveness to self-reflection practices.",
            "low",
            today - timedelta(days=10),
        ),
        (
            "growth",
            "Consistent improvement detected over the last 9 days. Cognitive distortions have decreased from 2-3 per entry to zero. Positive reframing language appearing in recent entries.",
            "low",
            today - timedelta(days=5),
        ),
    ]

    query = """
        INSERT INTO emotional_patterns (id, user_id, pattern_type, description, severity, detected_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO NOTHING
    """
    for index, (pattern_type, description, severity, detected_on) in enumerate(patterns, start=1):
        await conn.execute(
            query,
            fixed_uuid(3000 + index),
            user_id,
            pattern_type,
            description,
            severity,
            datetime(detected_on.year, detected_on.month, detected_on.day, 12, 0),
        )


async def seed_weekly_insight(conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    await conn.execute(
        """
        INSERT INTO weekly_insights (
            id, user_id, week_start, dominant_emotion, avg_sentiment,
            top_triggers, cbt_recommendation, generated_at
        )
        VALUES (
            $1, $2, $3, $4, $5,
            $6::jsonb, $7, $8
        )
        ON CONFLICT (id) DO NOTHING
        """,
        fixed_uuid(4001),
        user_id,
        monday,
        "joy",
        0.52,
        json.dumps(["academic pressure", "social isolation", "perfectionism", "sleep quality"]),
        "You have been catching and reframing cognitive distortions in real time this week - that is advanced CBT practice. This week, try a Behavioral Activation exercise: schedule one small activity each day that gives you a sense of achievement or pleasure, even if motivation is low. Action often precedes feeling, not the other way around.",
        datetime(today.year, today.month, today.day) - timedelta(days=2),
    )


async def main() -> None:
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        async with conn.transaction():
            print("Seeding demo user...")
            await ensure_schema(conn)
            await seed_demo_user(conn)

            print("Seeding 30 days of journal entries...")
            await seed_journal_entries(conn, DEMO_USER_ID)

            print("Seeding chat history...")
            await seed_chat_history(conn, DEMO_USER_ID)

            print("Seeding emotional patterns...")
            await seed_patterns(conn, DEMO_USER_ID)

            print("Seeding weekly insight...")
            await seed_weekly_insight(conn, DEMO_USER_ID)
    finally:
        await conn.close()

    print("")
    print("✅ Seed complete!")
    print("   Demo login: demo@mindmirror.app")
    print("   Password:   Demo1234!")
    print("   Open:       http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
