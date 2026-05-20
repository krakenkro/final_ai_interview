from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from backend.observability.langsmith import traceable, wrap_openai_client


BASE_DIR = Path(__file__).resolve().parents[2]
PROMPT_PATH = BASE_DIR / "backend" / "prompts" / "hr_resume_analysis.md"

load_dotenv(BASE_DIR / ".env")


def load_hr_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _provider_name() -> str:
    return (os.getenv("HR_ANALYSIS_PROVIDER") or "openai").strip().lower()


def _model_name() -> str:
    return (
        os.getenv("HR_ANALYSIS_MODEL")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    ).strip()


def _max_input_chars() -> int:
    raw = (os.getenv("HR_ANALYSIS_MAX_INPUT_CHARS") or "16000").strip()
    try:
        return max(4000, int(raw))
    except ValueError:
        return 16000


def _max_output_tokens() -> int:
    raw = (os.getenv("HR_ANALYSIS_MAX_OUTPUT_TOKENS") or "2200").strip()
    try:
        return max(800, int(raw))
    except ValueError:
        return 2200


def _truncate_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}\n\n[truncated]"


def _default_hr_analysis(status: str, *, provider: str = "", model: str = "", message: str = "") -> Dict[str, Any]:
    return {
        "status": status,
        "provider": provider,
        "model": model,
        "prompt_version": "hr_resume_analysis_v1",
        "message": message,
        "overall_match_score_pct": 0,
        "match_explanation": "",
        "candidate_level": "",
        "vacancy_level": "",
        "resume_quality_score_pct": 0,
        "ats_compatibility_score_pct": 0,
        "interview_probability_pct": 0,
        "hr_screening_probability_pct": 0,
        "salary_level_estimation": "",
        "market_competitiveness": "",
        "risk_of_rejection": "",
        "strong_sides": [],
        "weak_sides": [],
        "missing_skills": [],
        "strong_matches": [],
        "hr_concerns": [],
        "why_candidate_fits": [],
        "why_candidate_may_be_rejected": [],
        "what_raises_questions": [],
        "improvement_suggestions": [],
        "technologies_to_highlight": [],
        "technologies_to_learn": [],
        "hr_verdict": "",
        "ats_keyword_analysis": {
            "present_keywords": [],
            "missing_keywords": [],
            "keyword_density_assessment": "",
        },
        "rewritten_resume_fragments": [],
    }


def build_default_hr_analysis(
    status: str,
    *,
    provider: str = "",
    model: str = "",
    message: str = "",
) -> Dict[str, Any]:
    return _default_hr_analysis(status, provider=provider, model=model, message=message)


def _int_percent(value: Any) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(number, 100))


def _list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    payload: List[str] = []
    for item in value:
        normalized = str(item).strip()
        if normalized:
            payload.append(normalized)
    return payload


def _normalize_rewritten_fragments(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []

    payload: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        fragment = {
            "section_title": str(item.get("section_title", "")).strip(),
            "original_excerpt": str(item.get("original_excerpt", "")).strip(),
            "rewritten_version": str(item.get("rewritten_version", "")).strip(),
            "rationale": str(item.get("rationale", "")).strip(),
        }
        if fragment["section_title"] or fragment["rewritten_version"]:
            payload.append(fragment)
    return payload[:5]


def normalize_hr_analysis(payload: Dict[str, Any], *, provider: str, model: str) -> Dict[str, Any]:
    base = _default_hr_analysis("completed", provider=provider, model=model)
    ats_payload = payload.get("ats_keyword_analysis", {})
    if not isinstance(ats_payload, dict):
        ats_payload = {}

    base.update(
        {
            "overall_match_score_pct": _int_percent(payload.get("overall_match_score_pct")),
            "match_explanation": str(payload.get("match_explanation", "")).strip(),
            "candidate_level": str(payload.get("candidate_level", "")).strip(),
            "vacancy_level": str(payload.get("vacancy_level", "")).strip(),
            "resume_quality_score_pct": _int_percent(payload.get("resume_quality_score_pct")),
            "ats_compatibility_score_pct": _int_percent(payload.get("ats_compatibility_score_pct")),
            "interview_probability_pct": _int_percent(payload.get("interview_probability_pct")),
            "hr_screening_probability_pct": _int_percent(payload.get("hr_screening_probability_pct")),
            "salary_level_estimation": str(payload.get("salary_level_estimation", "")).strip(),
            "market_competitiveness": str(payload.get("market_competitiveness", "")).strip(),
            "risk_of_rejection": str(payload.get("risk_of_rejection", "")).strip(),
            "strong_sides": _list_of_strings(payload.get("strong_sides")),
            "weak_sides": _list_of_strings(payload.get("weak_sides")),
            "missing_skills": _list_of_strings(payload.get("missing_skills")),
            "strong_matches": _list_of_strings(payload.get("strong_matches")),
            "hr_concerns": _list_of_strings(payload.get("hr_concerns")),
            "why_candidate_fits": _list_of_strings(payload.get("why_candidate_fits")),
            "why_candidate_may_be_rejected": _list_of_strings(payload.get("why_candidate_may_be_rejected")),
            "what_raises_questions": _list_of_strings(payload.get("what_raises_questions")),
            "improvement_suggestions": _list_of_strings(payload.get("improvement_suggestions")),
            "technologies_to_highlight": _list_of_strings(payload.get("technologies_to_highlight")),
            "technologies_to_learn": _list_of_strings(payload.get("technologies_to_learn")),
            "hr_verdict": str(payload.get("hr_verdict", "")).strip(),
            "ats_keyword_analysis": {
                "present_keywords": _list_of_strings(ats_payload.get("present_keywords")),
                "missing_keywords": _list_of_strings(ats_payload.get("missing_keywords")),
                "keyword_density_assessment": str(
                    ats_payload.get("keyword_density_assessment", "")
                ).strip(),
            },
            "rewritten_resume_fragments": _normalize_rewritten_fragments(
                payload.get("rewritten_resume_fragments")
            ),
        }
    )
    return base


def _build_user_payload(
    *,
    session: Dict[str, Any],
    resume_text: str,
    vacancy_text: str,
    parser_summary: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    job_profile: Dict[str, Any],
    skill_gap_map: Dict[str, Any],
    interview_topics: List[Dict[str, Any]],
) -> str:
    limit = _max_input_chars()
    payload = {
        "session_context": {
            "role": session.get("role"),
            "seniority": session.get("seniority"),
            "interview_type": session.get("interview_type"),
            "interview_language": session.get("interview_language"),
        },
        "resume_text": _truncate_text(resume_text, limit),
        "vacancy_text": _truncate_text(vacancy_text, limit),
        "deterministic_intake_artifacts": {
            "parser_summary": parser_summary,
            "candidate_profile": candidate_profile,
            "job_profile": job_profile,
            "skill_gap_map": skill_gap_map,
            "interview_topics": interview_topics,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@traceable(run_type="chain", name="hr_resume_analysis")
def analyze_resume_vacancy_fit(
    *,
    session: Dict[str, Any],
    resume_text: str,
    vacancy_text: str,
    parser_summary: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    job_profile: Dict[str, Any],
    skill_gap_map: Dict[str, Any],
    interview_topics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    provider = _provider_name()
    model = _model_name()

    if not resume_text.strip():
        return _default_hr_analysis(
            "skipped",
            provider=provider,
            model=model,
            message="Resume text is empty, so HR analysis was skipped.",
        )
    if not vacancy_text.strip():
        return _default_hr_analysis(
            "skipped",
            provider=provider,
            model=model,
            message="Vacancy text is empty, so HR analysis was skipped.",
        )

    if provider != "openai":
        return _default_hr_analysis(
            "skipped",
            provider=provider,
            model=model,
            message=f"Unsupported HR analysis provider: {provider}",
        )

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return _default_hr_analysis(
            "skipped",
            provider=provider,
            model=model,
            message="OPENAI_API_KEY is not set, so HR analysis was skipped.",
        )

    client = wrap_openai_client(OpenAI(api_key=api_key))
    prompt = load_hr_prompt()
    user_payload = _build_user_payload(
        session=session,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        parser_summary=parser_summary,
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        skill_gap_map=skill_gap_map,
        interview_topics=interview_topics,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=_max_output_tokens(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_payload},
            ],
        )
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict):
            raise ValueError("HR analysis response is not a JSON object.")
        return normalize_hr_analysis(parsed, provider=provider, model=model)
    except Exception as exc:
        return _default_hr_analysis(
            "failed",
            provider=provider,
            model=model,
            message=f"HR analysis failed: {exc}",
        )
