from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

from rate_limit import limiter
from routes import analysis, auth, chat, journal
from services.claude_service import check_ollama_health
from services.memory_service import ensure_base_schema, ensure_chat_schema, init_pool
from services.sentiment_service import get_emotion_pipeline
from services.whisper_service import get_model
from seed import seed_demo_data

app = FastAPI(title="MindMirror API")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

frontend_port = os.environ.get("FRONTEND_PORT", "3000").strip() or "3000"
frontend_origin = os.environ.get("FRONTEND_ORIGIN", f"http://localhost:{frontend_port}").strip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(journal.router, prefix="/journal", tags=["journal"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
APP_VERSION = "1.0.0"


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(_request, _exc) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many attempts. Please wait a minute."})


@app.on_event("startup")
async def startup_event() -> None:
    ai_provider = os.environ.get("AI_PROVIDER", "ollama").strip().lower()
    if ai_provider == "groq":
        print("Using Groq API for AI (cloud mode)")
        if not os.environ.get("GROQ_API_KEY", "").strip():
            print("Warning: GROQ_API_KEY is not set")
    else:
        ollama_ready = False
        for attempt in range(10):
            if await check_ollama_health():
                ollama_ready = True
                break
            if attempt < 9:
                await asyncio.sleep(3)

        if ollama_ready:
            print("Ollama is ready!")
        else:
            print("Warning: Ollama not ready yet")

    pool = await init_pool()
    await ensure_base_schema()
    async with pool.acquire() as conn:
        await seed_demo_data(conn)
    await ensure_chat_schema()
    preload_results = await asyncio.gather(
        asyncio.to_thread(get_model),
        asyncio.to_thread(get_emotion_pipeline),
        return_exceptions=True,
    )
    for result in preload_results:
        if isinstance(result, Exception):
            print(f"Startup preload warning: {result}")


@app.get("/health")
async def health() -> dict[str, object]:
    """Return a structured health check response for container and orchestrator probes."""
    ai_provider = os.environ.get("AI_PROVIDER", "ollama").strip().lower() or "ollama"
    database_ready = False
    try:
        pool = await init_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        database_ready = True
    except Exception:
        database_ready = False

    ollama_ready = False
    if ai_provider == "ollama":
        ollama_ready = await check_ollama_health()

    return {
        "status": "ok",
        "ai_provider": ai_provider,
        "ollama_ready": ollama_ready,
        "database_ready": database_ready,
        "version": APP_VERSION,
    }
