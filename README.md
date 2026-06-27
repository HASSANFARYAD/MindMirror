# 🚀 Quick Start — No API Keys Needed

This app runs 100% locally. No Anthropic, OpenAI, or paid services required.

### Prerequisites
- Docker Desktop installed and running
- 8GB RAM minimum (for models)
- 10GB free disk space (for model downloads)

### Run in 3 steps

Step 1 — Clone and setup env
  cp .env.example .env

Step 2 — Build and start everything
  docker-compose up --build

Step 3 — Wait for models to download (first run only ~5 mins)
  Watch for: "Ollama is ready!" and "Whisper ready." in logs

Step 4 — Open the app
  Frontend: http://localhost:3000
  Backend API docs: http://localhost:8000/docs

### What downloads automatically on first run
- Llama 3.2 3B model (~2GB) via Ollama
- Whisper base model (~140MB)
- distilroberta emotion model (~300MB via HuggingFace)
All cached in Docker volumes — only downloads once.

# MindMirror

MindMirror is an AI-powered emotional health companion built around CBT principles. It helps users journal, reflect on patterns, and have supportive conversations grounded in cognitive reframing.

## Problem Statement

People often notice distress, anxiety, or negative self-talk only after it has already shaped their day. MindMirror gives them a low-friction way to capture emotions, identify recurring cognitive distortions, and turn reflection into a gentle next step.

## Features

- Mood journaling with CBT-grounded emotional analysis
- Real-time chat support with streaming responses
- Emotional dashboard with trends, patterns, and weekly insight summaries
- Growth Story view showing before-and-after emotional transformation
- Live Emotion Preview while typing in the journal
- Therapist Export with a printable private PDF summary
- Demo Mode for one-click presentation-ready walkthroughs

## Architecture

```text
                         +----------------------+
                         |   Next.js Frontend   |
                         |  Journal / Chat /    |
                         |  Dashboard / Landing |
                         +----------+-----------+
                                    |
                                    | HTTP + SSE
                                    v
                         +----------+-----------+
                         |    FastAPI Backend   |
                         | Auth / Analysis /    |
                         | Chat / Journal APIs   |
                         +----------+-----------+
                                    |
           +------------------------+------------------------+
           |                        |                        |
           v                        v                        v
   +---------------+        +---------------+        +---------------+
   |   Supabase    |        | Anthropic API |        | OpenAI Whisper|
   | PostgreSQL    |        | Claude chat   |        | voice transcribe|
   +---------------+        +---------------+        +---------------+
                                    |
                                    v
                            +---------------+
                            | Hugging Face   |
                            | emotion model  |
                            +---------------+
```

## Tech Stack

- Next.js 14 App Router
- TypeScript
- Tailwind CSS
- FastAPI
- Pydantic
- Supabase / PostgreSQL
- Anthropic Claude
- Hugging Face Transformers
- OpenAI Whisper
- SSE streaming
- Vitest + React Testing Library (frontend tests)
- pytest + pytest-asyncio (backend tests)

## Setup

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your keys.
3. Apply the Supabase schema from `backend/database/schema.sql`.
4. Start the app:

```bash
docker-compose up --build
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:8000`

## How the CBT AI Works

MindMirror applies CBT silently on each response:

1. It detects cognitive distortions such as catastrophizing, mind reading, or all-or-nothing thinking.
2. It validates the emotion before offering any reframing.
3. It asks one Socratic question to help the user examine the thought.
4. If distress appears high, it suggests a grounding technique.
5. It closes with a warm, concrete next step.

## Screenshots

Placeholder for product screenshots.

## Demo Video

Placeholder for a demo video link.

## Testing

### Backend (pytest)
```bash
cd backend && python -m pytest -v
```
114 tests covering auth, sentiment analysis, pattern detection, journal, chat, and security.

### Frontend (Vitest)
```bash
cd frontend && npm test
```
20 tests covering utility functions (`sentiment.ts`) and component rendering/interaction (`CrisisBanner.tsx`). Run `npm run test:watch` for watch mode.

Both suites run independently — no API keys or external services required.
