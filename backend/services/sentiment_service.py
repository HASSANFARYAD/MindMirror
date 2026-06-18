from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

from transformers import pipeline

logger = logging.getLogger(__name__)

_emotion_pipeline = None

DISTORTION_PATTERNS: dict[str, list[str]] = {
    "catastrophizing": [
        "worst",
        "terrible",
        "disaster",
        "ruined",
        "horrible",
        "everything is falling apart",
        "unbearable",
        "can't take it",
    ],
    "all_or_nothing": [
        "always",
        "never",
        "every time",
        "nothing works",
        "complete failure",
        "totally useless",
        "absolutely hopeless",
    ],
    "mind_reading": [
        "they think",
        "they must hate",
        "everyone knows",
        "they probably",
        "nobody cares",
        "they don't like me",
    ],
    "fortune_telling": [
        "i know it will",
        "it won't work",
        "i'll fail",
        "there's no point",
        "i'll never",
        "it's going to go wrong",
    ],
    "emotional_reasoning": [
        "i feel like a failure",
        "i feel worthless",
        "i feel stupid",
        "i feel like nobody",
        "i feel like i can't",
    ],
    "personalization": [
        "it's my fault",
        "i caused",
        "because of me",
        "i'm to blame",
        "i ruined everything",
    ],
    "should_statements": [
        "i should",
        "i must",
        "i have to",
        "i ought to",
        "i'm supposed to",
        "i need to be perfect",
    ],
    "overgeneralization": [
        "i always fail",
        "i never succeed",
        "things never work",
        "i can't do anything right",
    ],
}


def get_emotion_pipeline():
    global _emotion_pipeline
    if _emotion_pipeline is not None:
        return _emotion_pipeline

    try:
        print("Loading emotion pipeline...")
        _emotion_pipeline = pipeline(
            task="text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1,
        )
        print("Emotion pipeline ready.")
    except Exception as exc:  # pragma: no cover - external dependency fallback
        logger.exception("Failed to load emotion pipeline: %s", exc)
        _emotion_pipeline = None
    return _emotion_pipeline


def detect_distortions(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    matches: list[dict[str, Any]] = []
    for distortion_type, keywords in DISTORTION_PATTERNS.items():
        for keyword in keywords:
            if keyword in lowered:
                matches.append(
                    {
                        "type": distortion_type,
                        "evidence": keyword,
                        "confidence": 0.75,
                    }
                )
                break
    return matches


def _flatten_emotion_result(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        if result and isinstance(result[0], list):
            inner = result[0]
            return [item for item in inner if isinstance(item, dict)]
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        return [result]
    return []


def _fallback_analysis(text: str) -> dict[str, Any]:
    emotions = {
        "joy": 0.1,
        "sadness": 0.2,
        "anger": 0.1,
        "fear": 0.1,
        "disgust": 0.05,
    }
    lowered = text.lower()
    if any(word in lowered for word in ["happy", "good", "grateful", "relieved", "calm"]):
        emotions["joy"] = 0.5
    if any(word in lowered for word in ["sad", "upset", "hurt", "lonely", "cry"]):
        emotions["sadness"] = 0.5
    if any(word in lowered for word in ["angry", "mad", "furious", "annoyed"]):
        emotions["anger"] = 0.45
    if any(word in lowered for word in ["worried", "anxious", "afraid", "panic"]):
        emotions["fear"] = 0.45
    sentiment_score = round(emotions.get("joy", 0.0) - ((emotions.get("sadness", 0.0) + emotions.get("anger", 0.0) + emotions.get("fear", 0.0) + emotions.get("disgust", 0.0)) * 0.5), 3)
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    sentiment_label = "positive" if sentiment_score > 0.2 else "negative" if sentiment_score < -0.2 else "neutral"
    dominant_emotion = max(emotions.items(), key=lambda item: item[1])[0]
    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "dominant_emotion": dominant_emotion,
        "emotions": emotions,
        "cognitive_distortions": detect_distortions(text),
    }


async def _pipeline_analysis(text: str) -> dict[str, Any]:
    """Run the emotion pipeline when available and normalize the response."""
    pipe = get_emotion_pipeline()
    if pipe is None:
        return _fallback_analysis(text)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, pipe, text[:512])
    except RuntimeError:
        return _fallback_analysis(text)

    items = _flatten_emotion_result(result)
    emotions = {str(item.get("label", "")).lower(): float(item.get("score") or 0.0) for item in items if item.get("label")}
    if not emotions:
        return _fallback_analysis(text)

    positive = emotions.get("joy", 0.0)
    negative = emotions.get("sadness", 0.0) + emotions.get("anger", 0.0) + emotions.get("fear", 0.0) + emotions.get("disgust", 0.0)
    sentiment_score = round(positive - (negative * 0.5), 3)
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    sentiment_label = "positive" if sentiment_score > 0.2 else "negative" if sentiment_score < -0.2 else "neutral"
    dominant_emotion = max(emotions.items(), key=lambda item: item[1])[0]
    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "dominant_emotion": dominant_emotion,
        "emotions": emotions,
    }


async def analyze_entry(text: str) -> dict[str, Any]:
    try:
        result = await _pipeline_analysis(text)
        if "cognitive_distortions" not in result:
            result["cognitive_distortions"] = detect_distortions(text)
        return result
    except Exception as exc:  # pragma: no cover - external dependency fallback
        logger.exception("Emotion analysis failed: %s", exc)
        return _fallback_analysis(text)


async def analyze_preview(text: str) -> dict[str, Any]:
    """Return a lightweight preview without distortion analysis or persistence."""
    try:
        result = await _pipeline_analysis(text)
        return {
            "dominant_emotion": str(result.get("dominant_emotion") or "neutral"),
            "sentiment_score": float(result.get("sentiment_score") or 0.0),
        }
    except Exception as exc:  # pragma: no cover - external dependency fallback
        logger.exception("Emotion preview failed: %s", exc)
        fallback = _fallback_analysis(text)
        return {
            "dominant_emotion": str(fallback.get("dominant_emotion") or "neutral"),
            "sentiment_score": float(fallback.get("sentiment_score") or 0.0),
        }


def analyze_text(text: str) -> dict[str, Any]:
    try:
        return asyncio.run(analyze_entry(text))
    except RuntimeError:
        return _fallback_analysis(text)
