from __future__ import annotations

import json
from typing import Any, Dict, List

from fastmcp import FastMCP

from backend.services.hr_resume_ai import analyze_resume_vacancy_fit


mcp = FastMCP("HRResumeMCP")


def _parse_json_payload(raw: str, *, fallback: Any) -> Any:
    if not raw.strip():
        return fallback
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return value


@mcp.tool(description="Analyze resume and vacancy like an experienced IT recruiter and hiring manager.")
def analyze_resume_vacancy_fit_tool(
    session_json: str,
    parser_summary_json: str,
    candidate_profile_json: str,
    job_profile_json: str,
    skill_gap_map_json: str,
    interview_topics_json: str,
    resume_text: str,
    vacancy_text: str,
) -> Dict[str, Any]:
    session = _parse_json_payload(session_json, fallback={})
    parser_summary = _parse_json_payload(parser_summary_json, fallback={})
    candidate_profile = _parse_json_payload(candidate_profile_json, fallback={})
    job_profile = _parse_json_payload(job_profile_json, fallback={})
    skill_gap_map = _parse_json_payload(skill_gap_map_json, fallback={})
    interview_topics = _parse_json_payload(interview_topics_json, fallback=[])
    if not isinstance(session, dict):
        session = {}
    if not isinstance(parser_summary, dict):
        parser_summary = {}
    if not isinstance(candidate_profile, dict):
        candidate_profile = {}
    if not isinstance(job_profile, dict):
        job_profile = {}
    if not isinstance(skill_gap_map, dict):
        skill_gap_map = {}
    if not isinstance(interview_topics, list):
        interview_topics = []

    normalized_topics: List[Dict[str, Any]] = [
        item for item in interview_topics if isinstance(item, dict)
    ]

    return analyze_resume_vacancy_fit(
        session=session,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        parser_summary=parser_summary,
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        skill_gap_map=skill_gap_map,
        interview_topics=normalized_topics,
    )


if __name__ == "__main__":
    mcp.run(show_banner=False)
