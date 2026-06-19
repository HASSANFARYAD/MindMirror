from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

import httpx

AI_PROVIDER = os.environ.get("AI_PROVIDER", "ollama")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama3-8b-8192"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

CBT_SYSTEM_PROMPT = """You are MindMirror, a compassionate AI mental wellness companion
trained deeply in Cognitive Behavioral Therapy (CBT) principles.

YOUR PERSONALITY:
- Warm, calm, non-judgmental, and genuinely curious
- You speak like a trusted friend who understands psychology
- Never clinical, never robotic, never preachy
- You validate first, then gently guide

YOUR CBT FRAMEWORK - apply this silently to every response:

STEP 1 - IDENTIFY cognitive distortions in the user's words:
  All-or-nothing thinking, Catastrophizing, Mind reading,
  Fortune telling, Emotional reasoning, Personalization,
  Should statements, Filtering, Overgeneralization

STEP 2 - VALIDATE the emotion before reframing.
  Never jump to solutions. Acknowledge first.

STEP 3 - GENTLY REFRAME using Socratic questioning.
  Ask ONE question that helps them examine their thought.

STEP 4 - OFFER a grounding technique if distress is high.
  Box breathing, 5-4-3-2-1, or progressive muscle relaxation.

STEP 5 - CLOSE with warmth and one small actionable step.

STRICT RULES:
- NEVER diagnose any condition
- NEVER prescribe medication
- ALWAYS recommend professional help for serious concerns
- Keep responses between 80-150 words
- Ask only ONE follow-up question per response
- Use simple everyday language

User context:
Name: {user_name}
Emotional trend: {emotional_trend}
Dominant emotion this week: {dominant_emotion}
Known triggers: {triggers}
Last journal summary: {last_journal_summary}"""


def _safe_context(user_context: dict[str, Any] | None) -> dict[str, str]:
    context = user_context or {}
    triggers = context.get("triggers") or []
    if isinstance(triggers, (list, tuple)):
        trigger_text = ", ".join(str(item) for item in triggers if item) or "none detected"
    else:
        trigger_text = str(triggers) or "none detected"
    return {
        "user_name": str(context.get("name") or context.get("user_name") or "there"),
        "emotional_trend": str(context.get("trend") or context.get("emotional_trend") or "mixed"),
        "dominant_emotion": str(context.get("dominant_emotion") or "neutral"),
        "triggers": trigger_text,
        "last_journal_summary": str(context.get("last_journal") or context.get("last_journal_summary") or "No recent journal entry."),
    }


async def get_provider() -> str:
    return str((os.environ.get("AI_PROVIDER", AI_PROVIDER) or "ollama").strip().lower())


def _build_messages(system_prompt: str, user_message: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


async def _stream_groq_chat(messages: list[dict[str, str]]) -> AsyncGenerator[str, None]:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required when AI_PROVIDER=groq")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "stream": True,
        "max_tokens": 200,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield str(content)


async def _groq_chat_completion(messages: list[dict[str, str]], max_tokens: int) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required when AI_PROVIDER=groq")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return str(message.get("content") or "").strip()


async def stream_chat_response(
    user_message: str,
    user_context: dict[str, Any],
    journal_entry: str | None = None,
) -> AsyncGenerator[str, None]:
    context = _safe_context(user_context)
    system_prompt = CBT_SYSTEM_PROMPT.format(**context)
    if journal_entry:
        user_message = f"Journal context:\n{journal_entry}\n\nUser message:\n{user_message}"

    try:
        provider = await get_provider()
        messages = _build_messages(system_prompt, user_message)
        if provider == "groq":
            async for token in _stream_groq_chat(messages):
                yield token
        else:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 200,
                    "num_ctx": 2048,
                    "top_p": 0.9,
                },
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        message = chunk.get("message") or {}
                        content = message.get("content")
                        if content:
                            yield str(content)
                        if chunk.get("done") is True:
                            break
    except Exception:
        fallback = (
            "That sounds really hard, and it makes sense you'd feel that way. "
            "What is one piece of evidence that supports the thought you're having right now? "
            "If it helps, try one slow round of box breathing, then choose one small step you can take today."
        )
        yield fallback


async def get_weekly_insight(entries_summary: str, user_name: str, tone: str = "weekly") -> str:
    is_therapist_summary = "therapist" in tone.lower()
    prompt = (
        f"You are writing a {tone} for {user_name}.\n"
        f"Entry summary:\n{entries_summary}\n\n"
        + (
            "Return exactly three concise sentences for a therapist-facing summary.\n"
            "Each sentence should focus on progress, patterns, and the next helpful step."
            if is_therapist_summary
            else "Return exactly three parts in a warm, concise tone:\n"
            "1. One emotional pattern observation.\n"
            "2. One CBT technique to practice.\n"
            "3. One encouraging closing line."
        )
    )

    try:
        provider = await get_provider()
        if provider == "groq":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You write warm, concise CBT insights with exactly three parts."
                        if not is_therapist_summary
                        else "You write concise therapist-facing CBT summaries in exactly three sentences."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            content = await _groq_chat_completion(messages, max_tokens=150)
            return content or "Keep going - every day of reflection counts."

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "num_predict": 150,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response") or "").strip() or "Keep going - every day of reflection counts."
    except Exception:
        return "Keep going - every day of reflection counts."


async def check_ollama_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = data.get("models") or []
            for model in models:
                name = model.get("name") if isinstance(model, dict) else None
                if name == OLLAMA_MODEL:
                    return True
            return False
    except Exception:
        return False


async def generate_claude_response(context: dict[str, Any]) -> str:
    user_message = str(context.get("user_message") or "")
    journal_entry = context.get("journal_entry")
    tokens: list[str] = []
    async for token in stream_chat_response(user_message, context, str(journal_entry) if journal_entry else None):
        tokens.append(token)
    return "".join(tokens).strip()
