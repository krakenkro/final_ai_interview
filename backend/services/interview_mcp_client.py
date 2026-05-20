from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import Client

from backend.observability.langsmith import traceable


BASE_DIR = Path(__file__).resolve().parents[2]
PYTHON_BIN = BASE_DIR / ".venv" / "bin" / "python"

MCP_CONFIG = {
    "mcpServers": {
        "interview_kb_mcp": {
            "transport": "stdio",
            "command": str(PYTHON_BIN),
            "args": ["-m", "mcp_servers.interview_kb_mcp.server"],
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


@traceable(run_type="tool", name="search_interview_questions")
def search_interview_questions(
    *,
    topic: str,
    level: str,
    role: Optional[str],
    interview_type: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    payload = call_tool(
        "search_interview_questions",
        {
            "topic": topic,
            "level": level,
            "role": role,
            "interview_type": interview_type,
            "limit": limit,
        },
    )
    return payload if isinstance(payload, list) else []


@traceable(run_type="tool", name="get_topic_cheatsheet")
def get_topic_cheatsheet(
    *,
    topic: str,
    level: str,
    role: Optional[str],
    interview_type: str,
) -> Dict[str, Any]:
    payload = call_tool(
        "get_topic_cheatsheet",
        {
            "topic": topic,
            "level": level,
            "role": role,
            "interview_type": interview_type,
        },
    )
    return payload if isinstance(payload, dict) else {}


@traceable(run_type="tool", name="get_evaluation_rubric")
def get_evaluation_rubric(
    *,
    question_type: str,
    level: str,
    role: Optional[str],
) -> Dict[str, Any]:
    payload = call_tool(
        "get_evaluation_rubric",
        {
            "question_type": question_type,
            "level": level,
            "role": role,
        },
    )
    return payload if isinstance(payload, dict) else {}


@traceable(run_type="tool", name="get_followup_questions")
def get_followup_questions(
    *,
    topic: str,
    previous_answer_summary: str,
    level: str,
    role: Optional[str],
    interview_type: str,
    limit: int = 3,
) -> List[str]:
    payload = call_tool(
        "get_followup_questions",
        {
            "topic": topic,
            "previous_answer_summary": previous_answer_summary,
            "level": level,
            "role": role,
            "interview_type": interview_type,
            "limit": limit,
        },
    )
    return payload if isinstance(payload, list) else []
