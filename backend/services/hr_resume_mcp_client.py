from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from fastmcp import Client

from backend.observability.langsmith import traceable


BASE_DIR = Path(__file__).resolve().parents[2]
PYTHON_BIN = BASE_DIR / ".venv" / "bin" / "python"

MCP_CONFIG = {
    "mcpServers": {
        "hr_resume_mcp": {
            "transport": "stdio",
            "command": str(PYTHON_BIN),
            "args": ["-m", "mcp_servers.hr_resume_mcp.server"],
        }
    }
}


def _coerce_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _coerce_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_coerce_payload(item) for item in value]

    for attr in ("data", "structured_content", "content"):
        if hasattr(value, attr):
            attr_value = getattr(value, attr)
            if attr_value is not None:
                return _coerce_payload(attr_value)
    if hasattr(value, "text"):
        return getattr(value, "text")
    if hasattr(value, "model_dump"):
        return _coerce_payload(value.model_dump())
    return str(value)


async def _call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    async with Client(MCP_CONFIG) as client:
        result = await client.call_tool(name, arguments)
        return _coerce_payload(result)


def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    return asyncio.run(_call_tool(name, arguments))


@traceable(run_type="tool", name="analyze_resume_vacancy_fit_tool")
def analyze_resume_vacancy_fit(
    *,
    session: Dict[str, Any],
    parser_summary: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    job_profile: Dict[str, Any],
    skill_gap_map: Dict[str, Any],
    interview_topics: List[Dict[str, Any]],
    resume_text: str,
    vacancy_text: str,
) -> Dict[str, Any]:
    payload = call_tool(
        "analyze_resume_vacancy_fit_tool",
        {
            "session_json": json.dumps(session, ensure_ascii=False),
            "parser_summary_json": json.dumps(parser_summary, ensure_ascii=False),
            "candidate_profile_json": json.dumps(candidate_profile, ensure_ascii=False),
            "job_profile_json": json.dumps(job_profile, ensure_ascii=False),
            "skill_gap_map_json": json.dumps(skill_gap_map, ensure_ascii=False),
            "interview_topics_json": json.dumps(interview_topics, ensure_ascii=False),
            "resume_text": resume_text,
            "vacancy_text": vacancy_text,
        },
    )
    return payload if isinstance(payload, dict) else {}
