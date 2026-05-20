import re
from typing import Dict, List, Optional, Sequence

from backend.services.rag import retrieve_context


FALLBACK_QUESTION_BANK: Dict[str, Dict[str, List[str]]] = {
    "Frontend Developer": {
        "Technical Core": [
            "Explain the difference between state and props in React and give an example from a recent project.",
            "How would you diagnose a slow React page with too many rerenders?",
            "What trade-offs do you consider when choosing between client-side and server-side rendering?",
        ],
        "Behavioural": [
            "Tell me about a time you had to debug a production issue under pressure.",
            "Describe a disagreement with a designer or backend engineer and how you resolved it.",
            "What is one frontend decision you owned end-to-end and what did you learn from it?",
        ],
        "Mixed": [
            "Walk me through a frontend project from your resume and the hardest technical decision in it.",
            "How do JavaScript event loop knowledge and React rendering behavior affect UI performance?",
            "Tell me about a bug you shipped and how you handled the recovery.",
        ],
    },
    "Java Backend Developer": {
        "Technical Core": [
            "How do you explain transactions and isolation levels to a teammate using a real API example?",
            "What are the differences between HashMap and ConcurrentHashMap, and when would you choose each?",
            "How would you design a resilient REST endpoint that depends on a slow downstream service?",
        ],
        "Behavioural": [
            "Tell me about a backend incident you handled or a situation where you prevented one.",
            "Describe a case where you had to push back on a risky implementation decision.",
            "What is one delivery you are proud of and how did you communicate trade-offs?",
        ],
        "Mixed": [
            "Walk me through a backend project from your resume and the most important technical trade-off you made.",
            "How do Spring Boot, SQL design, and caching decisions work together in a typical service?",
            "Tell me about a time you improved reliability or performance in a backend system.",
        ],
    },
}

ROLE_TO_SLUG = {
    "Frontend Developer": "frontend_developer",
    "Java Backend Developer": "java_backend_developer",
}

INTERVIEW_TYPE_TO_SLUG = {
    "Technical Core": "technical_core",
    "Behavioural": "behavioural",
    "Mixed": "mixed",
}

TOPIC_QUERY_HINTS = {
    "JavaScript fundamentals": "javascript fundamentals",
    "TypeScript typing and narrowing": "typescript narrowing и typing",
    "Browser rendering and event loop": "browser rendering event loop",
    "Browser rendering and layout fundamentals": "browser rendering layout",
    "React component model": "react components state props",
    "State management and data flow": "state management data flow",
    "API integration and async flows": "api integration async flows",
    "Performance and optimization basics": "frontend performance optimization",
    "Testing fundamentals": "frontend testing fundamentals",
    "Resume-based project deep dive": "resume project deep dive",
    "Core Java and collections": "core java collections",
    "Spring Boot basics": "spring boot basics",
    "REST API design": "rest api design",
    "SQL and indexing basics": "sql indexing",
    "Transactions and data consistency": "transactions data consistency",
    "Concurrency and multithreading basics": "concurrency multithreading backend",
    "Caching basics": "backend caching",
    "Messaging and async communication basics": "messaging async communication backend",
    "ownership": "ownership и личная ответственность",
    "conflict resolution": "conflict resolution с коллегой",
    "failure / lessons learned": "failure lessons learned",
    "prioritization": "prioritization trade offs",
    "teamwork": "teamwork collaboration",
    "communication of trade-offs": "communication of trade offs",
    "incident handling / debugging stories": "incident debugging story",
}

DEFAULT_TOPIC_FALLBACKS = {
    "Frontend Developer": [
        "React component model",
        "TypeScript typing and narrowing",
        "API integration and async flows",
        "Performance and optimization basics",
    ],
    "Java Backend Developer": [
        "Spring Boot basics",
        "SQL and indexing basics",
        "Transactions and data consistency",
        "Concurrency and multithreading basics",
    ],
}

BEHAVIOURAL_TOPICS = [
    "ownership",
    "conflict resolution",
    "prioritization",
    "failure / lessons learned",
    "communication of trade-offs",
    "incident handling / debugging stories",
]


def _session_filters(session_data: Dict[str, object], *, force_cross_role: bool = False) -> Dict[str, str]:
    session = session_data["session"]
    interview_type = str(session["interview_type"])
    use_cross_role = force_cross_role or interview_type == "Behavioural"
    return {
        "role": "cross_role" if use_cross_role else ROLE_TO_SLUG.get(str(session["role"]), "frontend_developer"),
        "seniority": str(session["seniority"]).strip().lower(),
        "interview_type": INTERVIEW_TYPE_TO_SLUG.get(interview_type, "mixed"),
        "layer": "processed",
    }


def _normalize_topic_name(topic: str) -> str:
    topic = topic.strip()
    return TOPIC_QUERY_HINTS.get(topic, topic)


def _analysis_topics(session_data: Dict[str, object]) -> List[str]:
    interview_type = str(session_data["session"].get("interview_type") or "Mixed")
    analysis = session_data.get("analysis", {})
    technical_topics = [str(item.get("topic", "")).strip() for item in analysis.get("interview_topics", []) if item.get("topic")]

    if interview_type == "Behavioural":
        return BEHAVIOURAL_TOPICS

    if interview_type == "Mixed":
        merged: List[str] = []
        for topic in technical_topics[:3]:
            if topic and topic not in merged:
                merged.append(topic)
        for topic in BEHAVIOURAL_TOPICS[:2]:
            if topic not in merged:
                merged.append(topic)
        if merged:
            return merged

    role = str(session_data["session"]["role"])
    if technical_topics:
        return technical_topics
    return DEFAULT_TOPIC_FALLBACKS.get(role, DEFAULT_TOPIC_FALLBACKS["Frontend Developer"])


def _max_questions(session_data: Dict[str, object]) -> int:
    topics = _analysis_topics(session_data)
    duration = int(session_data["session"].get("duration_minutes") or 15)
    duration_cap = 3 if duration <= 15 else 4 if duration <= 25 else 5
    return max(3, min(duration_cap, len(topics) or 3))


def _topic_for_cursor(session_data: Dict[str, object], cursor: int) -> str:
    topics = _analysis_topics(session_data)
    if not topics:
        return "Resume-based project deep dive"
    if cursor < len(topics):
        return topics[cursor]
    return topics[-1]


def _extract_questions(text: str) -> List[str]:
    questions: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`")
        if not line:
            continue
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        candidate = numbered_match.group(1).strip() if numbered_match else bullet_match.group(1).strip() if bullet_match else ""
        if not candidate:
            continue
        if candidate.endswith("?") or candidate.lower().startswith(
            (
                "tell me",
                "walk me",
                "describe",
                "how ",
                "what ",
                "why ",
                "when ",
                "расскажи",
                "опиши",
                "объясни",
                "приведи",
                "как ",
                "что ",
                "почему ",
                "когда ",
            )
        ):
            questions.append(candidate)
    return questions


def _extract_followups(text: str) -> List[str]:
    prompts: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`")
        if not line:
            continue
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        candidate = numbered_match.group(1).strip() if numbered_match else bullet_match.group(1).strip() if bullet_match else ""
        if candidate:
            prompts.append(candidate)
    return prompts


def _used_questions(session_data: Dict[str, object]) -> set[str]:
    used = {str(turn.get("question", "")).strip() for turn in session_data.get("turns", [])}
    current_question = str(session_data["session"].get("current_question") or "").strip()
    if current_question:
        used.add(current_question)
    return used


def _pick_first_unused(candidates: Sequence[str], used_questions: set[str]) -> Optional[str]:
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized and normalized not in used_questions:
            return normalized
    return candidates[0].strip() if candidates else None


def _retrieve_question_candidates(session_data: Dict[str, object], topic: str) -> List[Dict[str, object]]:
    filters = _session_filters(session_data)
    results = retrieve_context(
        _normalize_topic_name(topic),
        top_k=6,
        role=filters["role"],
        seniority=filters["seniority"],
        interview_type=filters["interview_type"],
        document_types=["question_bank", "answer_outline", "theory_note", "cheatsheet"],
        layer=filters["layer"],
    )
    if results and results[0].get("status") not in {"no_match", "index_missing"}:
        return results

    if filters["interview_type"] in {"behavioural", "mixed"}:
        cross_role_filters = _session_filters(session_data, force_cross_role=True)
        return retrieve_context(
            _normalize_topic_name(topic),
            top_k=6,
            role=cross_role_filters["role"],
            seniority=cross_role_filters["seniority"],
            interview_type=cross_role_filters["interview_type"],
            document_types=["question_bank", "answer_outline", "theory_note", "cheatsheet"],
            layer=cross_role_filters["layer"],
        )

    return results


def _retrieve_followup_candidates(session_data: Dict[str, object], topic: str) -> List[Dict[str, object]]:
    filters = _session_filters(session_data)
    results = retrieve_context(
        _normalize_topic_name(topic),
        top_k=6,
        role=filters["role"],
        seniority=filters["seniority"],
        interview_type=filters["interview_type"],
        document_types=["followup_bank", "answer_outline", "rubric"],
        layer=filters["layer"],
    )
    if results and results[0].get("status") not in {"no_match", "index_missing"}:
        return results

    if filters["interview_type"] in {"behavioural", "mixed"}:
        cross_role_filters = _session_filters(session_data, force_cross_role=True)
        return retrieve_context(
            _normalize_topic_name(topic),
            top_k=6,
            role=cross_role_filters["role"],
            seniority=cross_role_filters["seniority"],
            interview_type=cross_role_filters["interview_type"],
            document_types=["followup_bank", "answer_outline", "rubric"],
            layer=cross_role_filters["layer"],
        )

    return results


def _fallback_question(session_data: Dict[str, object], cursor: int) -> str:
    session = session_data["session"]
    role = str(session["role"])
    interview_type = str(session["interview_type"])
    questions = FALLBACK_QUESTION_BANK.get(role, FALLBACK_QUESTION_BANK["Frontend Developer"]).get(
        interview_type,
        FALLBACK_QUESTION_BANK["Frontend Developer"]["Mixed"],
    )
    index = min(cursor, len(questions) - 1)
    return questions[index]


def _build_question_from_context(session_data: Dict[str, object], topic: str, cursor: int) -> str:
    used_questions = _used_questions(session_data)
    results = _retrieve_question_candidates(session_data, topic)
    extracted_questions: List[str] = []
    for result in results:
        extracted_questions.extend(_extract_questions(str(result.get("text", ""))))

    selected = _pick_first_unused(extracted_questions, used_questions)
    if selected:
        return selected

    return _fallback_question(session_data, cursor)


def _compose_followup_question(current_question: str, prompt: str, topic: str = "") -> str:
    cleaned_prompt = prompt.strip().strip("`")
    lowered = cleaned_prompt.lower()
    cleaned_question = current_question.strip().rstrip("?")

    if cleaned_prompt.endswith("?"):
        return cleaned_prompt

    if "request-response flow" in lowered:
        if cleaned_question.lower().startswith("как "):
            cleaned_question = cleaned_question[4:].strip()
        return f"Как request-response flow связан с тем, как {cleaned_question} под капотом?"
    if "loading/success/error" in lowered:
        return "Как бы ты организовал loading, success и error состояния вокруг этого сценария?"
    if "headers/status/cors" in lowered:
        return "Какие headers, status codes или CORS-ограничения здесь важно учитывать?"
    if "ux or correctness trade-off" in lowered:
        return "Какой здесь есть компромисс между UX и корректностью?"
    if "поведение клиента при ошибке" in lowered:
        return "Как должен вести себя клиент, если запрос завершился ошибкой?"

    if lowered.startswith(("объясни", "опиши", "расскажи", "как ", "что ", "почему ", "зачем ", "какие ", "какой ")):
        return cleaned_prompt if cleaned_prompt.endswith("?") else f"{cleaned_prompt}?"

    if topic:
        return f'Можешь раскрыть аспект "{cleaned_prompt}" и связать его с темой "{topic}"?'
    return f'Можешь раскрыть аспект "{cleaned_prompt}" и связать его с предыдущим вопросом?'


def _build_followup_question(session_data: Dict[str, object], topic: str, current_question: str) -> str:
    results = _retrieve_followup_candidates(session_data, topic)
    prompts: List[str] = []
    for result in results:
        prompts.extend(_extract_followups(str(result.get("text", ""))))

    prompt = prompts[0] if prompts else "Раскрой ответ глубже: добавь конкретный пример, trade-offs, риски и итог."
    return _compose_followup_question(current_question, prompt, topic)


def _build_feedback(answer_text: str, *, used_followup: bool) -> str:
    word_count = len(answer_text.strip().split())
    lowered = answer_text.lower()

    has_example = any(marker in lowered for marker in ("example", "например", "например,", "for example", "случа", "project", "проек"))
    has_tradeoff = any(marker in lowered for marker in ("trade-off", "tradeoff", "компром", "выбор", "risk", "риск"))
    has_result = any(marker in lowered for marker in ("result", "итог", "в итоге", "impact", "результ"))

    strengths: List[str] = []
    gaps: List[str] = []

    if word_count >= 40:
        strengths.append("ответ уже достаточно развёрнут")
    else:
        gaps.append("не хватает глубины")

    if has_example:
        strengths.append("есть конкретика или проектный контекст")
    else:
        gaps.append("нужен пример из опыта")

    if has_tradeoff:
        strengths.append("видно понимание компромиссов и ограничений")
    else:
        gaps.append("стоит явнее назвать компромиссы или риски")

    if has_result:
        strengths.append("прозвучал результат и эффект решения")
    else:
        gaps.append("не хватает итогов и влияния решения")

    if used_followup:
        prefix = "Follow-up принят."
    else:
        prefix = "Ответ сохранён."

    strengths_text = "; ".join(strengths[:2]) if strengths else "есть базовый сигнал по теме"
    gaps_text = "; ".join(gaps[:2]) if gaps else "критичных пробелов в формате ответа не видно"
    return f"{prefix} Сильные стороны: {strengths_text}. Что улучшить: {gaps_text}."


def build_first_question(session_data: Dict[str, object]) -> str:
    topic = _topic_for_cursor(session_data, 0)
    return _build_question_from_context(session_data, topic, 0)


def evaluate_answer(session_data: Dict[str, object], answer_text: str) -> Dict[str, object]:
    session = session_data["session"]
    cursor = int(session["question_cursor"])
    current_question = str(session.get("current_question") or build_first_question(session_data))
    current_topic = _topic_for_cursor(session_data, cursor)
    answer_word_count = len(answer_text.strip().split())

    if answer_word_count < 20:
        return {
            "feedback": _build_feedback(answer_text, used_followup=True),
            "next_question": _build_followup_question(session_data, current_topic, current_question),
            "next_cursor": cursor,
            "status": "in_progress",
        }

    next_cursor = cursor + 1
    max_questions = _max_questions(session_data)
    if next_cursor >= max_questions:
        return {
            "feedback": _build_feedback(answer_text, used_followup=False),
            "next_question": None,
            "next_cursor": next_cursor,
            "status": "completed",
        }

    next_topic = _topic_for_cursor(session_data, next_cursor)
    next_question = _build_question_from_context(session_data, next_topic, next_cursor)
    return {
        "feedback": _build_feedback(answer_text, used_followup=False),
        "next_question": next_question,
        "next_cursor": next_cursor,
        "status": "in_progress",
    }
