from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.observability.langsmith import traceable
from backend.services.evaluator import build_heuristic_evaluation
from backend.services.mock_interview import (
    _analysis_topics,
    _build_feedback,
    _build_followup_question,
    _build_question_from_context,
    _max_questions,
    _question_key,
)
from backend.services.interview_coach import build_coaching_report
from backend.services.interview_mcp_client import (
    get_evaluation_rubric,
    get_followup_questions,
    get_topic_cheatsheet,
    search_interview_questions,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InterviewGraphState(TypedDict, total=False):
    event: Literal["start", "answer"]
    session_data: Dict[str, Any]
    answer_text: str
    cursor: int
    current_question: str
    current_topic: str
    interview_plan: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    feedback: str
    next_question: Optional[str]
    next_cursor: int
    status: str
    final_report: Dict[str, Any]
    trace: List[Dict[str, Any]]
    routing_decision: Literal["followup", "next_topic", "report"]
    tool_context: Dict[str, Any]


def _append_trace(state: InterviewGraphState, node: str, summary: str, **extra: Any) -> None:
    trace = list(state.get("trace", []))
    event = {
        "node": node,
        "summary": summary,
        "timestamp": utc_now(),
    }
    if extra:
        event["details"] = extra
    trace.append(event)
    state["trace"] = trace


def _topic_priority(topic: str, session_data: Dict[str, Any]) -> str:
    skill_gap_map = session_data.get("analysis", {}).get("skill_gap_map", {})
    recommended_focus = {str(item).strip() for item in skill_gap_map.get("recommended_focus", [])}
    missing_skills = {str(item).strip() for item in skill_gap_map.get("missing_skills", [])}
    topic_lower = topic.lower()
    if any(skill.lower() in topic_lower for skill in recommended_focus | missing_skills):
        return "high"
    return "medium"


def _build_interview_plan(session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    session = session_data["session"]
    topics = _analysis_topics(session_data)
    max_questions = _max_questions(session_data)
    plan: List[Dict[str, Any]] = []
    for index, topic in enumerate(topics[:max_questions]):
        plan.append(
            {
                "topic_index": index,
                "topic": topic,
                "priority": _topic_priority(topic, session_data),
                "interview_type": session["interview_type"],
                "expected_difficulty": str(session["seniority"]).lower(),
            }
        )
    return plan


def _session_tool_args(session_data: Dict[str, Any]) -> Dict[str, str]:
    session = session_data["session"]
    role = str(session.get("role", "Frontend Developer"))
    role_map = {
        "Frontend Developer": "frontend_developer",
    }
    interview_type_map = {
        "Technical Core": "technical_core",
        "Behavioural": "behavioural",
        "Mixed": "mixed",
    }
    return {
        "role": "cross_role" if str(session.get("interview_type")) == "Behavioural" else role_map.get(role, "frontend_developer"),
        "level": str(session.get("seniority", "middle")).lower(),
        "interview_type": interview_type_map.get(str(session.get("interview_type")), "mixed"),
    }


def _safe_search_questions(session_data: Dict[str, Any], topic: str, limit: int = 3) -> List[Dict[str, Any]]:
    args = _session_tool_args(session_data)
    try:
        return search_interview_questions(
            topic=topic,
            level=args["level"],
            role=args["role"],
            interview_type=args["interview_type"],
            limit=limit,
        )
    except Exception:
        return []


def _safe_get_cheatsheet(session_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
    args = _session_tool_args(session_data)
    try:
        return get_topic_cheatsheet(
            topic=topic,
            level=args["level"],
            role=args["role"],
            interview_type=args["interview_type"],
        )
    except Exception:
        return {}


def _safe_get_rubric(session_data: Dict[str, Any]) -> Dict[str, Any]:
    args = _session_tool_args(session_data)
    try:
        return get_evaluation_rubric(
            question_type=args["interview_type"],
            level=args["level"],
            role=args["role"],
        )
    except Exception:
        return {}


def _safe_get_followups(session_data: Dict[str, Any], topic: str, previous_answer_summary: str) -> List[str]:
    args = _session_tool_args(session_data)
    try:
        return get_followup_questions(
            topic=topic,
            previous_answer_summary=previous_answer_summary,
            level=args["level"],
            role=args["role"],
            interview_type=args["interview_type"],
            limit=3,
        )
    except Exception:
        return []


def _looks_like_question(value: str) -> bool:
    candidate = value.strip()
    lowered = candidate.lower()
    if candidate.endswith("?"):
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


def _humanize_gap(value: str) -> str:
    labels = {
        "answer_too_short": "ответ слишком короткий",
        "missing_example": "не хватает примера из опыта",
        "missing_tradeoff": "не озвучены компромиссы",
        "missing_result": "не сформулирован итог",
        "weak_structure": "ответу не хватает структуры",
    }
    normalized = value.strip()
    return labels.get(normalized, normalized.replace("_", " "))


def _build_evaluation(state: InterviewGraphState) -> Dict[str, Any]:
    answer_text = state.get("answer_text", "")
    current_question = state.get("current_question", "")
    current_topic = state.get("current_topic", "")
    suggested_follow_up = _build_followup_question(state["session_data"], current_topic, current_question, answer_text)
    return build_heuristic_evaluation(
        answer_text,
        current_question=current_question,
        current_topic=current_topic,
        follow_up_suggestion=suggested_follow_up,
    )


def _build_final_report(session_data: Dict[str, Any], latest_evaluation: Dict[str, Any]) -> Dict[str, Any]:
    turns = session_data.get("turns", [])
    scores: List[int] = []
    workflow = session_data.get("workflow", {})
    previous_evaluation = workflow.get("last_evaluation", {})
    if isinstance(previous_evaluation.get("score_0_10"), int):
        scores.append(int(previous_evaluation["score_0_10"]))
    if isinstance(latest_evaluation.get("score_0_10"), int):
        scores.append(int(latest_evaluation["score_0_10"]))

    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    all_answers = " ".join(str(turn.get("answer", "")) for turn in turns)
    strong_points: List[str] = []
    gaps: List[str] = list(latest_evaluation.get("detected_gaps", []))

    if "trade" in all_answers.lower() or "компром" in all_answers.lower():
        strong_points.append("Кандидат проговаривает компромиссы и ограничения.")
    if "в итоге" in all_answers.lower() or "result" in all_answers.lower():
        strong_points.append("В ответах виден outcome и эффект решений.")
    if not strong_points:
        strong_points.append("Есть базовая тематическая релевантность по ходу интервью.")

    review_topics = _analysis_topics(session_data)[:3]
    return {
        "summary": "Интервью завершено. Ниже сохранён краткий разбор по ответам и темам для повторения.",
        "final_score_0_10": average_score,
        "score_by_category": {
            "latest_answer": latest_evaluation.get("score_0_10", 0),
            "session_average": average_score,
        },
        "strengths": strong_points[:3],
        "gaps": [_humanize_gap(item) for item in gaps[:4]],
        "topics_to_review": review_topics,
        "questions_to_practice": [str(turn.get("question", "")) for turn in turns[-3:]],
    }


def planner_node(state: InterviewGraphState) -> InterviewGraphState:
    session_data = state["session_data"]
    plan = session_data.get("workflow", {}).get("interview_plan") or _build_interview_plan(session_data)
    cursor = int(session_data["session"].get("question_cursor") or 0)
    topic_index = min(cursor, len(plan) - 1) if plan else 0
    current_topic = plan[topic_index]["topic"] if plan else "Resume-based project deep dive"
    question_candidates = _safe_search_questions(session_data, current_topic, limit=2)

    state["interview_plan"] = plan
    state["cursor"] = cursor
    state["current_topic"] = current_topic
    state["tool_context"] = {
        "planner_question_candidates": question_candidates,
    }
    _append_trace(
        state,
        "planner",
        "Interview plan resolved for current step.",
        topic=current_topic,
        cursor=cursor,
        tool_call="search_interview_questions",
        tool_results_count=len(question_candidates),
    )
    return state


def interviewer_node(state: InterviewGraphState) -> InterviewGraphState:
    event = state["event"]
    session_data = state["session_data"]
    cursor = int(state.get("cursor", 0))
    current_topic = state.get("current_topic", "Resume-based project deep dive")

    if event == "answer" and state.get("routing_decision") == "followup":
        next_question = str(state["evaluation"]["suggested_follow_up"])
    else:
        next_question = _build_question_from_context(session_data, current_topic, cursor)

    state["next_question"] = next_question
    state["next_cursor"] = cursor
    state["status"] = "in_progress"
    _append_trace(
        state,
        "interviewer",
        "Next interviewer prompt prepared.",
        next_question=next_question,
        used_mcp_candidates=bool(state.get("tool_context", {}).get("planner_question_candidates")),
    )
    return state


def evaluator_node(state: InterviewGraphState) -> InterviewGraphState:
    evaluation = _build_evaluation(state)
    rubric = _safe_get_rubric(state["session_data"])
    cheatsheet = _safe_get_cheatsheet(state["session_data"], state.get("current_topic", ""))
    evaluation["rubric_context"] = rubric
    evaluation["topic_cheatsheet"] = {
        "topic": cheatsheet.get("topic"),
        "source": cheatsheet.get("sources", []),
    }
    state["evaluation"] = evaluation
    _append_trace(
        state,
        "evaluator",
        "Answer evaluated.",
        score_0_10=evaluation["score_0_10"],
        follow_up_needed=evaluation["follow_up_needed"],
        tool_calls=["get_evaluation_rubric", "get_topic_cheatsheet"],
    )
    return state


def feedback_node(state: InterviewGraphState) -> InterviewGraphState:
    answer_text = state.get("answer_text", "")
    current_question = str(state.get("current_question") or state["session_data"]["session"].get("current_question") or "")
    previous_evaluation = state["session_data"].get("workflow", {}).get("last_evaluation", {})
    previous_suggested_followup = str(previous_evaluation.get("suggested_follow_up") or "").strip()
    used_followup = bool(
        previous_suggested_followup
        and _question_key(current_question) == _question_key(previous_suggested_followup)
    )
    feedback = _build_feedback(
        answer_text,
        used_followup=used_followup,
        evaluation=state.get("evaluation", {}),
    )
    state["feedback"] = feedback
    _append_trace(state, "feedback", "Feedback text prepared.")
    return state


def decision_node(state: InterviewGraphState) -> InterviewGraphState:
    session_data = state["session_data"]
    session = session_data["session"]
    evaluation = state["evaluation"]
    cursor = int(session.get("question_cursor") or 0)
    current_question = str(session.get("current_question") or "")
    turns = session_data.get("turns", [])
    previous_evaluation = session_data.get("workflow", {}).get("last_evaluation", {})
    previous_suggested_followup = str(previous_evaluation.get("suggested_follow_up") or "").strip()
    current_followup_count = 1 if previous_suggested_followup and _question_key(current_question) == _question_key(previous_suggested_followup) else 0
    max_questions = _max_questions(session_data)
    next_topic_index = cursor + 1

    if evaluation["follow_up_needed"] and current_followup_count < 1:
        followup_candidates = _safe_get_followups(state["session_data"], state.get("current_topic", ""), state.get("answer_text", ""))
        state["routing_decision"] = "followup"
        state["next_cursor"] = cursor
        state["status"] = "in_progress"
        _append_trace(
            state,
            "decision",
            "Routing to follow-up loop.",
            followup_count=current_followup_count + 1,
            tool_call="get_followup_questions",
            tool_results_count=len(followup_candidates),
        )
        return state

    if next_topic_index >= max_questions or len(turns) + 1 >= max_questions:
        state["routing_decision"] = "report"
        state["next_cursor"] = next_topic_index
        state["status"] = "completed"
        _append_trace(state, "decision", "Interview will complete after this answer.", next_topic_index=next_topic_index)
        return state

    state["routing_decision"] = "next_topic"
    state["cursor"] = next_topic_index
    next_topic = state["interview_plan"][next_topic_index]["topic"] if state.get("interview_plan") else "Resume-based project deep dive"
    state["current_topic"] = next_topic
    state["next_cursor"] = next_topic_index
    state["status"] = "in_progress"
    tool_context = dict(state.get("tool_context", {}))
    tool_context["planner_question_candidates"] = _safe_search_questions(state["session_data"], next_topic, limit=2)
    state["tool_context"] = tool_context
    _append_trace(
        state,
        "decision",
        "Routing to next topic.",
        next_topic=next_topic,
        next_topic_index=next_topic_index,
        tool_call="search_interview_questions",
    )
    return state


def report_node(state: InterviewGraphState) -> InterviewGraphState:
    report = _build_final_report(state["session_data"], state.get("evaluation", {}))
    coaching_report = build_coaching_report(
        strengths=report.get("strengths", []),
        weaknesses=report.get("gaps", []),
        improvements=report.get("topics_to_review", []),
        drills=report.get("questions_to_practice", []),
    )
    report["coaching"] = coaching_report
    state["final_report"] = report
    state["next_question"] = None
    state["status"] = "completed"
    _append_trace(
        state,
        "report",
        "Final report prepared.",
        final_score_0_10=report["final_score_0_10"],
        skill_used="Interview Coach",
    )
    return state


def _route_from_start(state: InterviewGraphState) -> str:
    return "planner"


def _route_after_planner(state: InterviewGraphState) -> str:
    return "interviewer" if state["event"] == "start" else "evaluator"


def _route_after_decision(state: InterviewGraphState) -> str:
    return state.get("routing_decision", "report")


def build_graph():
    graph = StateGraph(InterviewGraphState)
    graph.add_node("planner", planner_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("decision", decision_node)
    graph.add_node("report", report_node)

    graph.add_conditional_edges(
        START,
        _route_from_start,
        {
            "planner": "planner",
        },
    )
    graph.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "interviewer": "interviewer",
            "evaluator": "evaluator",
        },
    )
    graph.add_edge("interviewer", END)
    graph.add_edge("evaluator", "feedback")
    graph.add_edge("feedback", "decision")
    graph.add_conditional_edges(
        "decision",
        _route_after_decision,
        {
            "followup": "interviewer",
            "next_topic": "interviewer",
            "report": "report",
        },
    )
    graph.add_edge("report", END)
    return graph.compile()


GRAPH = build_graph()


@traceable(run_type="chain", name="run_start_workflow")
def run_start_workflow(session_data: Dict[str, Any]) -> Dict[str, Any]:
    state: InterviewGraphState = {
        "event": "start",
        "session_data": session_data,
        "trace": [],
    }
    result = GRAPH.invoke(state)
    return {
        "interview_plan": result.get("interview_plan", []),
        "trace": result.get("trace", []),
        "next_question": result.get("next_question"),
        "next_cursor": int(result.get("next_cursor", 0)),
        "status": result.get("status", "in_progress"),
    }


@traceable(run_type="chain", name="run_answer_workflow")
def run_answer_workflow(session_data: Dict[str, Any], answer_text: str) -> Dict[str, Any]:
    state: InterviewGraphState = {
        "event": "answer",
        "session_data": session_data,
        "answer_text": answer_text,
        "current_question": str(session_data["session"].get("current_question") or ""),
        "trace": [],
    }
    result = GRAPH.invoke(state)
    return {
        "interview_plan": result.get("interview_plan", []),
        "trace": result.get("trace", []),
        "feedback": result.get("feedback", ""),
        "next_question": result.get("next_question"),
        "next_cursor": int(result.get("next_cursor", session_data["session"].get("question_cursor") or 0)),
        "status": result.get("status", "in_progress"),
        "evaluation": result.get("evaluation", {}),
        "final_report": result.get("final_report", {}),
    }
