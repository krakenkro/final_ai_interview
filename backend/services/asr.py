from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

from backend.observability.langsmith import traceable, wrap_openai_client


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "backend" / "storage" / "uploads"

load_dotenv(BASE_DIR / ".env")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to `.env` before using voice mode.")
    return wrap_openai_client(OpenAI(api_key=api_key))


def _language_code(interview_language: Optional[str]) -> Optional[str]:
    value = str(interview_language or "").strip().lower()
    if value in {"russian", "ru", "русский"}:
        return "ru"
    if value in {"english", "en", "английский"}:
        return "en"
    return None


def save_audio_file(session_id: str, filename: str, audio_bytes: bytes) -> str:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename or "answer.webm").suffix or ".webm"
    target = UPLOADS_DIR / f"{session_id}_voice_{_utc_stamp()}{suffix}"
    target.write_bytes(audio_bytes)
    return str(target)


@traceable(run_type="tool", name="asr_transcribe_audio")
def transcribe_audio(
    audio_path: str,
    *,
    interview_language: Optional[str] = None,
    model: str = "whisper-1",
) -> Dict[str, Any]:
    source = Path(audio_path)
    if not source.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = _get_openai_client()
    language = _language_code(interview_language)

    with source.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            language=language or None,
            response_format="json",
        )

    transcript = result.text if hasattr(result, "text") else str(result)
    return {
        "status": "completed",
        "provider": "openai",
        "model": model,
        "language": language or "auto",
        "audio_path": str(source),
        "transcript": transcript.strip(),
    }
