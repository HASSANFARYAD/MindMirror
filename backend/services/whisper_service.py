from __future__ import annotations

import asyncio
import logging
import os
import tempfile

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency fallback
    WhisperModel = None

logger = logging.getLogger(__name__)

_model = None


def get_model():
    global _model
    if _model is not None:
        return _model

    if WhisperModel is None:
        logger.warning("Whisper dependency is not installed; voice transcription will be disabled.")
        return None

    model_name = os.environ.get("WHISPER_MODEL", "base")
    # tiny  = fastest, lowest accuracy, best for weak CPU
    # base  = balanced (recommended default)
    # small = better accuracy, slower on CPU
    print(f"Loading Whisper {model_name} model...")
    _model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print("Whisper ready.")
    return _model


async def transcribe_audio(audio_bytes: bytes, file_extension: str = "webm") -> str:
    if WhisperModel is None:
        return ""

    temp_path = None
    try:
        suffix = f".{file_extension.lstrip('.') or 'webm'}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        def transcribe_fn():
            model = get_model()
            if model is None:
                return {"text": ""}
            segments, _info = model.transcribe(temp_path, language="en", beam_size=1, vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments if getattr(segment, "text", "")).strip()
            return {"text": text}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, transcribe_fn)
        return str(result.get("text") or "").strip()
    except Exception as exc:  # pragma: no cover - external dependency fallback
        logger.exception("Whisper transcription failed: %s", exc)
        return ""
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                logger.exception("Failed to remove temporary audio file: %s", temp_path)
