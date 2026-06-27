# MindMirror

AI-powered emotional health companion built around CBT principles. Journal, reflect on patterns, and get supportive conversations grounded in cognitive reframing — all running **100% locally** with no paid API keys.

## Quick Start

### Prerequisites
- Docker Desktop
- 8GB RAM minimum
- 10GB free disk space (model downloads, first run only)

### Run
```bash
cp .env.example .env
docker-compose up --build
```

Wait for `"Ollama is ready!"` and `"Whisper ready."` in logs (~5 mins first run).

- **Frontend:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

## Features

- **CBT-grounded journaling** — emotion analysis via HuggingFace + 8 cognitive distortion detectors
- **AI chat assistant** — streaming LLM (Ollama local or Groq cloud) with a 5-step CBT framework
- **Emotional dashboard** — sentiment timeline, radar chart, mood calendar, patterns, weekly insights
- **Growth Story** — before/after comparison of oldest vs newest entries with auto-generated narrative
- **Live emotion preview** — emoji overlay while typing in the journal
- **Voice journaling** — Whisper STT (local, CPU int8)
- **Therapist export** — printable clinical summary
- **Pattern detection** — triggers, weekly cycles, growth streaks, alert conditions
- **Email verification** — via Resend (auto-sent on register, manual resend available)
- **Offline-first PWA** — service worker with caching, manifest, installable
- **Dark glassmorphism UI** — custom gradients, animations, responsive
- **Demo mode** — 30-day 3-phase emotional arc with deterministic seed data

## Architecture

```text
                        +----------------------+
                        |   Next.js Frontend   |
                        |  Journal / Chat /    |
                        |  Dashboard / Landing |
                        +---------+-----------+
                                  |
                            HTTP + SSE
                                  v
                        +---------+-----------+
                        |    FastAPI Backend   |
                        | Auth / Analysis /    |
                        | Chat / Journal APIs  |
                        +---------+-----------+
                                  |
            +---------------------+----------------------+
            |                     |                       |
            v                     v                       v
    +---------------+     +---------------+       +---------------+
    |  PostgreSQL   |     | Ollama / Groq |       |   Whisper     |
    |  (asyncpg)    |     |  LLM (CBT)    |       |   STT model   |
    +---------------+     +---------------+       +---------------+
            |                     |
            v                     v
    +---------------+     +---------------+
    |  Alembic      |     | Hugging Face  |
    |  migrations   |     | emotion model |
    +---------------+     +---------------+
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Pydantic, asyncpg, Python 3.11 |
| AI | Ollama (local) or Groq (cloud) for LLM, HuggingFace for emotion, Whisper for STT |
| Database | PostgreSQL, Alembic migrations |
| Auth | JWT in HttpOnly cookies, bcrypt, rate-limited |
| PWA | Service worker with Cache API, manifest.json, offline indicator |
| Email | Resend API (optional — no key = silent skip) |
| Testing | Vitest + RTL (frontend), pytest + pytest-asyncio (backend) |

## Environment Variables

See `.env.example` for all options. Key ones:

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `JWT_SECRET` | Yes | — | Random string for token signing |
| `AI_PROVIDER` | No | `ollama` | Switch to `groq` for cloud mode |
| `GROQ_API_KEY` | No | — | Required if `AI_PROVIDER=groq` |
| `DATABASE_URL` | No | Docker default | Cloud DB connection string |
| `RESEND_API_KEY` | No | — | Optional — enables email verification |
| `RESEND_FROM_EMAIL` | No | `onboarding@resend.dev` | Sender address |

## How the CBT AI Works

Each chat response silently applies a 5-step framework:

1. **Detect** cognitive distortions (catastrophizing, mind reading, all-or-nothing, etc.)
2. **Validate** the emotion before reframing
3. **Ask** one Socratic question to examine the thought
4. **Ground** if distress is high (breathing, sensory check-in)
5. **Close** with a warm, concrete next step

## Testing

### Frontend (Vitest)
```bash
cd frontend && npm test
```
20 tests: utility functions (`sentiment.ts`) + component rendering (`CrisisBanner.tsx`).

### Backend (pytest)
```bash
cd backend && python3 -m pytest -v
```
114 tests: auth, sentiment, patterns, journal, chat, security. In-memory mock DB, no external services needed.

## Project Structure

```
backend/
  main.py              — FastAPI entry point, CORS, startup
  alembic/             — Database migrations
  routes/              — auth, journal, chat, analysis
  services/            — memory, sentiment, claude, whisper, pattern, email, migration
  models/              — Pydantic schemas
  database/            — schema.sql (reference)
  tests/               — 114 pytest tests
frontend/
  app/                 — Next.js App Router pages
  components/          — React components
  lib/                 — API client, auth, sentiment helpers
  tests/               — 20 Vitest tests
  public/              — Static assets, manifest, service worker
```

## License

MIT
