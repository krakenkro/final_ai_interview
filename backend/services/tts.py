from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import fal_client
import httpx

from backend.observability.langsmith import traceable


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


def _require_fal_key() -> None:
    api_key = os.getenv("FAL_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FAL_KEY is not set. Add it to `.env` before using fal.ai TTS.")


def _fal_model() -> str:
    return os.getenv("FAL_TTS_MODEL", "fal-ai/minimax/speech-02-hd").strip() or "fal-ai/minimax/speech-02-hd"


def _fal_language(interview_language: Optional[str]) -> str:
    explicit = os.getenv("FAL_TTS_LANGUAGE", "").strip()
    if explicit:
        return explicit

    value = str(interview_language or "").strip().lower()
    if value in {"russian", "ru", "русский"}:
        return "Russian"
    if value in {"english", "en", "английский"}:
        return "English"
    return "auto"


def _download_audio_bytes(url: str) -> bytes:
    response = httpx.get(url, timeout=120.0)
    response.raise_for_status()
    return response.content


@traceable(run_type="tool", name="tts_synthesize_speech")
def synthesize_speech(
    text: str,
    *,
    interview_language: Optional[str] = None,
    model: Optional[str] = None,
    voice: Optional[str] = None,
    response_format: str = "mp3",
) -> Dict[str, Any]:
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("Text for speech synthesis is empty.")

    _require_fal_key()
    selected_model = model or _fal_model()
    language_boost = _fal_language(interview_language)

    arguments: Dict[str, Any] = {
        "text": normalized_text,
        "language_boost": language_boost,
        "output_format": "url",
        "audio_setting": {
            "format": response_format,
        },
    }
    if voice:
        arguments["voice_setting"] = {"voice_id": voice}

    result = fal_client.subscribe(
        selected_model,
        arguments=arguments,
    )
    audio = result.get("audio") or {}
    audio_url = str(audio.get("url") or "").strip()
    if not audio_url:
        raise RuntimeError("fal.ai TTS did not return an audio URL.")

    audio_bytes = _download_audio_bytes(audio_url)

    return {
        "status": "completed",
        "provider": "fal",
        "model": selected_model,
        "voice": voice or str((result.get("voice_setting") or {}).get("voice_id") or "default"),
        "mime_type": "audio/mpeg" if response_format == "mp3" else f"audio/{response_format}",
        "text": normalized_text,
        "language": language_boost,
        "audio_url": audio_url,
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
    }
