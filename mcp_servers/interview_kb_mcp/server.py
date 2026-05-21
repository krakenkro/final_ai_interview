from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from backend.services.rag import retrieve_context


mcp = FastMCP("InterviewKBMCP")


def _canonical_level(level: str) -> str:
    value = (level or "").strip().lower()
    if value in {"jun", "junior", "jr"}:
        return "junior"
    if value in {"mid", "middle", "middle-level"}:
        return "middle"
    return value or "middle"


def _canonical_question_type(value: str) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "technical": "technical_core",
        "technical core": "technical_core",
        "technical_core": "technical_core",
        "behavioral": "behavioural",
        "behavioural": "behavioural",
        "mixed": "mixed",
    }
    return aliases.get(normalized, normalized or "mixed")


def _canonical_role(role: Optional[str], question_type: str) -> str:
    if not role:
        return "cross_role" if question_type == "behavioural" else "frontend_developer"

    normalized = role.strip().lower()
    aliases = {
        "frontend developer": "frontend_developer",
        "frontend_developer": "frontend_developer",
        "cross_role": "cross_role",
        "cross-role": "cross_role",
    }
    if normalized in aliases:
        return aliases[normalized]
    return "cross_role" if question_type == "behavioural" else "frontend_developer"


def _extract_questions(text: str) -> List[str]:
    questions: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`")
        if not line:
            continue
        match = re.match(r"^\d+\.\s+(.*)$", line)
        if not match:
            continue
        candidate = match.group(1).strip()
        if candidate and _looks_like_question(candidate):
            questions.append(candidate)
    return questions


def _looks_like_question(candidate: str) -> bool:
    value = candidate.strip()
    lowered = value.lower()
    if value.endswith("?"):
        return True
    return lowered.startswith(
        (
            "tell me",
            "walk me through",
            "walk me",
            "describe",
            "explain",
            "how ",
            "what ",
            "why ",
            "when ",
            "which ",
            "расскажи",
            "опиши",
            "объясни",
            "приведи",
            "как ",
            "что ",
            "почему ",
            "когда ",
            "зачем ",
            "какую ",
            "какие ",
            "какой ",
        )
    )


def _extract_bullets(text: str) -> List[str]:
    bullets: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`")
        if not line:
            continue
        numbered = re.match(r"^\d+\.\s+(.*)$", line)
        bullet = re.match(r"^[-*]\s+(.*)$", line)
        candidate = numbered.group(1).strip() if numbered else bullet.group(1).strip() if bullet else ""
        if candidate:
            bullets.append(candidate)
    return bullets


def _clean_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [result for result in results if result.get("status") not in {"no_match", "index_missing"}]


@mcp.tool(description="Search the curated interview knowledge base for topic-specific interview questions.")
def search_interview_questions(
    topic: str,
    level: str,
    limit: int = 5,
    role: Optional[str] = None,
    interview_type: str = "technical_core",
) -> List[Dict[str, Any]]:
    question_type = _canonical_question_type(interview_type)
    role_slug = _canonical_role(role, question_type)
    results = _clean_results(
        retrieve_context(
            topic,
            top_k=max(limit, 5),
            role=role_slug,
            seniority=_canonical_level(level),
            interview_type=question_type,
            document_types=["question_bank"],
            layer="processed",
        )
    )

    payload: List[Dict[str, Any]] = []
    for result in results:
        questions = _extract_questions(str(result.get("text", "")))
        if not questions:
            continue
        payload.append(
            {
                "topic": result.get("topic"),
                "title": result.get("title"),
                "document_type": result.get("document_type"),
                "path": result.get("path"),
                "retrieval_backend": result.get("retrieval_backend"),
                "questions": questions[:limit],
                "excerpt": str(result.get("text", ""))[:600],
            }
        )
    return payload[:limit]


@mcp.tool(description="Return a concise cheatsheet or theory-note summary for an interview topic.")
def get_topic_cheatsheet(
    topic: str,
    role: Optional[str] = None,
    level: str = "middle",
    interview_type: str = "technical_core",
) -> Dict[str, Any]:
    question_type = _canonical_question_type(interview_type)
    role_slug = _canonical_role(role, question_type)
    results = _clean_results(
        retrieve_context(
            topic,
            top_k=3,
            role=role_slug,
            seniority=_canonical_level(level),
            interview_type=question_type,
            document_types=["cheatsheet", "theory_note"],
            layer="processed",
        )
    )
    if not results:
        return {"topic": topic, "summary": "", "highlights": [], "sources": []}

    primary = results[0]
    highlights = _extract_bullets(str(primary.get("text", "")))[:8]
    return {
        "topic": primary.get("topic"),
        "title": primary.get("title"),
        "summary": str(primary.get("text", ""))[:900],
        "highlights": highlights,
        "sources": [result.get("path") for result in results],
        "retrieval_backend": primary.get("retrieval_backend"),
    }


@mcp.tool(description="Load an evaluation rubric for a question/interview type and seniority level.")
def get_evaluation_rubric(
    question_type: str,
    level: str,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    type_slug = _canonical_question_type(question_type)
    role_slug = _canonical_role(role, type_slug)

    if type_slug == "behavioural":
        topic_query = "behavioural middle rubric" if _canonical_level(level) == "middle" else "behavioural junior rubric"
        role_slug = "cross_role"
    else:
        topic_query = f"{role_slug} {type_slug} {_canonical_level(level)} rubric"

    results = _clean_results(
        retrieve_context(
            topic_query,
            top_k=3,
            role=role_slug,
            seniority=_canonical_level(level),
            interview_type=type_slug,
            document_types=["rubric"],
            layer="processed",
        )
    )
    if not results:
        return {"question_type": type_slug, "level": _canonical_level(level), "criteria": [], "summary": ""}

    primary = results[0]
    criteria = _extract_bullets(str(primary.get("text", "")))[:10]
    return {
        "question_type": type_slug,
        "level": _canonical_level(level),
        "role": role_slug,
        "topic": primary.get("topic"),
        "criteria": criteria,
        "summary": str(primary.get("text", ""))[:900],
        "source_path": primary.get("path"),
        "retrieval_backend": primary.get("retrieval_backend"),
    }


@mcp.tool(description="Return candidate follow-up questions using only the curated follow-up bank.")
def get_followup_questions(
    topic: str,
    previous_answer_summary: str = "",
    level: str = "middle",
    role: Optional[str] = None,
    interview_type: str = "mixed",
    limit: int = 3,
) -> List[str]:
    question_type = _canonical_question_type(interview_type)
    role_slug = _canonical_role(role, question_type)
    query = topic if not previous_answer_summary else f"{topic}. {previous_answer_summary}"
    results = _clean_results(
        retrieve_context(
            query,
            top_k=5,
            role=role_slug,
            seniority=_canonical_level(level),
            interview_type=question_type,
            document_types=["followup_bank"],
            layer="processed",
        )
    )

    prompts: List[str] = []
    for result in results:
        prompts.extend(_extract_questions(str(result.get("text", ""))))

    deduped: List[str] = []
    seen = set()
    for prompt in prompts:
        normalized = prompt.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped[:limit]


if __name__ == "__main__":
    mcp.run(show_banner=False)
