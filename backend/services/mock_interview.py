import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]

from backend.observability.langsmith import traceable, wrap_openai_client
from backend.services.rag import retrieve_context


BASE_DIR = Path(__file__).resolve().parents[2]
QUESTION_PHRASING_PROMPT_PATH = BASE_DIR / "backend" / "prompts" / "question_final_phrasing.md"

load_dotenv(BASE_DIR / ".env")


FALLBACK_QUESTION_BANK: Dict[str, Dict[str, List[str]]] = {
    "Frontend Developer": {
        "Technical Core": [
            "Как вы обычно решаете, что во Vue-приложении должно стать отдельным компонентом?",
            "В каком случае вы бы выбрали Nuxt 3, а в каком хватило бы обычного SPA на Vue?",
            "Как вы обычно разделяете ошибки сети, ошибки доступа и ошибки бизнес-логики в интерфейсе?",
        ],
        "Behavioural": [
            "Расскажи про ситуацию, когда тебе пришлось разбирать продовый баг под давлением времени.",
            "Опиши разногласие с дизайнером или backend-разработчиком и как ты его разрешила.",
            "Какое фронтенд-решение ты довела до конца сама и чему тебя это научило?",
        ],
        "Mixed": [
            "Расскажи про фронтенд-проект из резюме и самое сложное техническое решение в нём.",
            "Как обновление состояния во Vue или Nuxt в итоге превращается в работу браузера?",
            "Расскажи про баг, который ты довела до продакшена, и как ты потом восстанавливала ситуацию.",
        ],
    },
}

ROLE_TO_SLUG = {
    "Frontend Developer": "frontend_developer",
}

INTERVIEW_TYPE_TO_SLUG = {
    "Technical Core": "technical_core",
    "Behavioural": "behavioural",
    "Mixed": "mixed",
}

TOPIC_QUERY_HINTS = {
    "Vue 3 component model": "vue props emits slots components",
    "Vue reactivity and refs": "vue computed watch ref reactive",
    "Nuxt 3 fundamentals": "nuxt ssr csr ssg hydration middleware",
    "Nuxt routing and data fetching": "nuxt routing usefetch useasyncdata data fetching",
    "TypeScript in frontend apps": "typescript frontend unions narrowing generics",
    "Browser rendering and event loop": "browser rendering event loop",
    "API integration and async flows": "api integration async flows",
    "Performance and optimization basics": "frontend performance optimization",
    "Resume-based project deep dive": "resume project deep dive",
    "ownership": "ownership и личная ответственность",
    "conflict resolution": "conflict resolution с коллегой",
    "failure / lessons learned": "failure lessons learned",
    "prioritization": "prioritization trade offs",
    "teamwork": "teamwork collaboration",
    "communication of trade-offs": "communication of trade offs",
    "incident handling / debugging stories": "incident debugging story",
}

TOPIC_MATCH_HINTS = {
    "Vue 3 component model": {"vue", "component", "props", "emits", "slots"},
    "Vue reactivity and refs": {"vue", "computed", "watch", "ref", "reactive", "composable"},
    "Nuxt 3 fundamentals": {"nuxt", "ssr", "csr", "ssg", "hydration", "middleware"},
    "Nuxt routing and data fetching": {"nuxt", "routing", "fetch", "usefetch", "useasyncdata", "hydration"},
    "TypeScript in frontend apps": {"typescript", "type", "union", "narrowing", "generic", "constraint"},
    "API integration and async flows": {"api", "fetch", "http", "request", "response", "cors", "retry"},
    "Browser rendering and event loop": {"browser", "rendering", "layout", "paint", "reflow", "event", "loop", "jank"},
    "Performance and optimization basics": {"performance", "optimization", "layout", "paint", "jank", "hydration"},
    "Resume-based project deep dive": {"resume", "project", "ownership", "debugging"},
    "ownership": {"ownership"},
    "conflict resolution": {"conflict"},
    "prioritization": {"prioritization", "priority"},
    "failure / lessons learned": {"failure", "lesson"},
    "communication of trade-offs": {"trade", "компром"},
    "incident handling / debugging stories": {"incident", "debugging", "debug"},
}

DEFAULT_TOPIC_FALLBACKS = {
    "Frontend Developer": [
        "Vue 3 component model",
        "Nuxt 3 fundamentals",
        "TypeScript in frontend apps",
        "API integration and async flows",
        "Performance and optimization basics",
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

QUESTION_MAX_CHARS = 220
QUESTION_PHRASING_RECENT_LIMIT = 4
QUESTION_BANNED_FRAGMENTS = (
    "strong answer patterns",
    "good topics for this outline",
    "retrieval tags",
    "follow-up ideas",
    "follow-up prompts",
    "request-response flow",
    "loading/success/error",
    "headers/status/cors",
)
QUESTION_SIMILARITY_STOPWORDS = {
    "как",
    "что",
    "какой",
    "какая",
    "какие",
    "какое",
    "какую",
    "когда",
    "почему",
    "зачем",
    "ты",
    "тебе",
    "твой",
    "твоему",
    "мнению",
    "этот",
    "эта",
    "это",
    "эту",
    "вообще",
    "обычно",
    "можешь",
    "могла",
    "бы",
    "ли",
    "считаешь",
    "является",
    "самым",
    "самой",
}


def _load_question_phrasing_prompt() -> str:
    return QUESTION_PHRASING_PROMPT_PATH.read_text(encoding="utf-8")


def _question_phrasing_enabled() -> bool:
    value = str(os.getenv("QUESTION_PHRASING_ENABLED", "true")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _question_phrasing_provider() -> str:
    return (os.getenv("QUESTION_PHRASING_PROVIDER") or "openai").strip().lower()


def _question_phrasing_model() -> str:
    return (
        os.getenv("QUESTION_PHRASING_MODEL")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    ).strip()


def _question_phrasing_temperature() -> float:
    raw = (os.getenv("QUESTION_PHRASING_TEMPERATURE") or "0.15").strip()
    try:
        value = float(raw)
    except ValueError:
        return 0.15
    return max(0.0, min(value, 1.0))


def _question_phrasing_max_tokens() -> int:
    raw = (os.getenv("QUESTION_PHRASING_MAX_TOKENS") or "120").strip()
    try:
        value = int(raw)
    except ValueError:
        return 120
    return max(40, min(value, 300))


def _truncate_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


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


def _looks_like_question(candidate: str) -> bool:
    value = candidate.strip()
    lowered = value.lower()
    if value.endswith("?"):
        return True
    return lowered.startswith(
        (
            "tell me",
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
        if _looks_like_question(candidate):
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
        if candidate and _looks_like_question(candidate):
            prompts.append(candidate)
    return prompts


def _question_key(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("follow-up:", "").strip()
    normalized = normalized.rstrip("?")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[\"“”«»]", "", normalized)
    return normalized


def _used_questions(session_data: Dict[str, object]) -> set[str]:
    used = {_question_key(str(turn.get("question", ""))) for turn in session_data.get("turns", []) if turn.get("question")}
    current_question = str(session_data["session"].get("current_question") or "").strip()
    if current_question:
        used.add(_question_key(current_question))
    return used


def _recent_questions(session_data: Dict[str, object], *, limit: int = QUESTION_PHRASING_RECENT_LIMIT) -> List[str]:
    recent: List[str] = []
    for turn in session_data.get("turns", []):
        question = str(turn.get("question", "")).strip()
        if question:
            recent.append(question)
    current_question = str(session_data["session"].get("current_question") or "").strip()
    if current_question:
        recent.append(current_question)
    if len(recent) <= limit:
        return recent
    return recent[-limit:]


def _question_similarity_key(value: str) -> str:
    normalized = re.sub(r"[^a-zа-я0-9\s_-]+", " ", value.lower())
    tokens = [
        token
        for token in normalized.split()
        if len(token) > 2 and token not in QUESTION_SIMILARITY_STOPWORDS
    ]
    return " ".join(tokens)


def _is_too_similar_to_recent(candidate: str, recent_questions: Sequence[str]) -> bool:
    candidate_key = _question_similarity_key(candidate)
    if not candidate_key:
        return False

    for question in recent_questions:
        other_key = _question_similarity_key(question)
        if not other_key:
            continue
        similarity = SequenceMatcher(None, candidate_key, other_key).ratio()
        if similarity >= 0.74:
            return True
    return False


def _has_repeated_phrase_loop(value: str) -> bool:
    normalized = re.sub(r"[^a-zа-я0-9\s/_-]+", " ", value.lower())
    tokens = [token for token in normalized.split() if len(token) > 2]
    if len(tokens) < 4:
        return False

    for size in (4, 3, 2):
        counts: Dict[str, int] = {}
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index:index + size])
            if len(phrase) < 12:
                continue
            counts[phrase] = counts.get(phrase, 0) + 1
            if counts[phrase] >= 2:
                return True
    return False


def _sanitize_question(candidate: str) -> Optional[str]:
    cleaned = re.sub(r"\s+", " ", candidate.strip().strip("`")).strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if any(fragment in lowered for fragment in QUESTION_BANNED_FRAGMENTS):
        return None
    if _has_repeated_phrase_loop(cleaned):
        return None
    if len(cleaned) > QUESTION_MAX_CHARS:
        return None
    if not _looks_like_question(cleaned):
        return None
    return cleaned if cleaned.endswith("?") else f"{cleaned}?"


def _result_matches_topic(result: Dict[str, object], topic: str) -> bool:
    tokens = TOPIC_MATCH_HINTS.get(topic, set())
    if not tokens:
        return True

    haystack = " ".join(
        [
            str(result.get("topic", "")),
            str(result.get("title", "")),
            str(result.get("path", "")),
        ]
    ).lower()
    return any(token in haystack for token in tokens)


def _pick_first_unused(candidates: Sequence[str], used_questions: set[str]) -> Optional[str]:
    for candidate in candidates:
        sanitized = _sanitize_question(candidate)
        if not sanitized:
            continue
        if _question_key(sanitized) not in used_questions:
            return sanitized
    for candidate in candidates:
        sanitized = _sanitize_question(candidate)
        if sanitized:
            return sanitized
    return None


def _normalize_candidate_question(candidate: str) -> str:
    return re.sub(r"\s+", " ", candidate.strip().strip("`")).strip()


def _extract_question_from_response(content: str) -> Optional[str]:
    text = content.strip()
    if not text:
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        question = str(payload.get("question", "")).strip()
        if question:
            return question

    fenced_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if fenced_match:
        try:
            payload = json.loads(fenced_match.group(0))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            question = str(payload.get("question", "")).strip()
            if question:
                return question

    return text.strip("` \n")


def _question_phrasing_input(
    *,
    session_data: Dict[str, object],
    topic: str,
    question_kind: str,
    candidate_question: str,
    current_question: str = "",
    answer_text: str = "",
    gap_intent: str = "",
) -> str:
    session = session_data["session"]
    payload: Dict[str, Any] = {
        "role": session.get("role"),
        "seniority": session.get("seniority"),
        "interview_type": session.get("interview_type"),
        "topic": topic,
        "question_kind": question_kind,
        "candidate_question": candidate_question,
        "already_asked_questions": _recent_questions(session_data),
        "max_length_chars": QUESTION_MAX_CHARS,
    }
    if current_question:
        payload["current_question"] = current_question
    if answer_text:
        payload["previous_answer_summary"] = _truncate_text(answer_text, 320)
    if gap_intent:
        payload["gap_intent"] = gap_intent
    return json.dumps(payload, ensure_ascii=False, indent=2)


@traceable(run_type="chain", name="phrase_interview_question")
def _phrase_question_with_llm(
    *,
    session_data: Dict[str, object],
    topic: str,
    question_kind: str,
    candidate_question: str,
    current_question: str = "",
    answer_text: str = "",
    gap_intent: str = "",
) -> Optional[str]:
    if not _question_phrasing_enabled():
        return None

    provider = _question_phrasing_provider()
    if provider != "openai" or OpenAI is None:
        return None

    api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)
        client = wrap_openai_client(client)
        response = client.chat.completions.create(
            model=_question_phrasing_model(),
            temperature=_question_phrasing_temperature(),
            max_tokens=_question_phrasing_max_tokens(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _load_question_phrasing_prompt()},
                {
                    "role": "user",
                    "content": _question_phrasing_input(
                        session_data=session_data,
                        topic=topic,
                        question_kind=question_kind,
                        candidate_question=candidate_question,
                        current_question=current_question,
                        answer_text=answer_text,
                        gap_intent=gap_intent,
                    ),
                },
            ],
        )
    except Exception:
        return None

    message = response.choices[0].message.content if response.choices else ""
    if not message:
        return None
    return _extract_question_from_response(message)


def _finalize_question(
    *,
    session_data: Dict[str, object],
    topic: str,
    question_kind: str,
    candidate_question: str,
    used_questions: set[str],
    current_question: str = "",
    answer_text: str = "",
    gap_intent: str = "",
) -> Optional[str]:
    normalized_candidate = _normalize_candidate_question(candidate_question)
    if not normalized_candidate:
        return None

    candidate_sanitized = _sanitize_question(normalized_candidate)
    recent_questions = _recent_questions(session_data)
    phrased = _phrase_question_with_llm(
        session_data=session_data,
        topic=topic,
        question_kind=question_kind,
        candidate_question=normalized_candidate,
        current_question=current_question,
        answer_text=answer_text,
        gap_intent=gap_intent,
    )
    if phrased:
        sanitized_phrased = _sanitize_question(phrased)
        if (
            sanitized_phrased
            and _question_key(sanitized_phrased) not in used_questions
            and not _is_too_similar_to_recent(sanitized_phrased, recent_questions)
        ):
            return sanitized_phrased

    if candidate_sanitized and not _is_too_similar_to_recent(candidate_sanitized, recent_questions):
        return candidate_sanitized
    return None


def _retrieve_question_candidates(session_data: Dict[str, object], topic: str) -> List[Dict[str, object]]:
    filters = _session_filters(session_data)
    results = retrieve_context(
            _normalize_topic_name(topic),
            top_k=6,
            role=filters["role"],
            seniority=filters["seniority"],
            interview_type=filters["interview_type"],
            document_types=["question_bank"],
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
            document_types=["question_bank"],
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
            document_types=["followup_bank"],
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
            document_types=["followup_bank"],
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
    normalized = _normalize_candidate_question(questions[index])
    return _sanitize_question(normalized) or normalized


def _build_question_from_context(session_data: Dict[str, object], topic: str, cursor: int) -> str:
    used_questions = _used_questions(session_data)
    results = _retrieve_question_candidates(session_data, topic)
    extracted_questions: List[str] = []
    for result in results:
        if not _result_matches_topic(result, topic):
            continue
        extracted_questions.extend(_extract_questions(str(result.get("text", ""))))

    for candidate in extracted_questions:
        sanitized = _sanitize_question(candidate)
        if not sanitized:
            continue
        if _question_key(sanitized) in used_questions:
            continue
        finalized = _finalize_question(
            session_data=session_data,
            topic=topic,
            question_kind="main",
            candidate_question=sanitized,
            used_questions=used_questions,
        )
        if finalized:
            return finalized

    fallback = _fallback_question(session_data, cursor)
    return (
        _finalize_question(
            session_data=session_data,
            topic=topic,
            question_kind="main",
            candidate_question=fallback,
            used_questions=used_questions,
        )
        or fallback
    )


def _infer_followup_intent(answer_text: str) -> str:
    lowered = answer_text.lower()
    word_count = len(answer_text.strip().split())
    if word_count < 20:
        return "mechanism"
    if not any(marker in lowered for marker in ("например", "example", "for example", "проект", "кейc", "кейс")):
        return "example"
    if not any(marker in lowered for marker in ("компром", "trade-off", "tradeoff", "риск", "выбор")):
        return "tradeoff"
    return "deepen"


def _fallback_followup_question(answer_text: str, topic: str) -> str:
    intent = _infer_followup_intent(answer_text)
    fallbacks = {
        "mechanism": "Можешь разобрать это пошагово и связать с реальным сценарием?",
        "example": "Можешь показать это на конкретном примере из проекта?",
        "tradeoff": "Какой компромисс ты здесь учитывала и от чего отказалась?",
        "deepen": f"Можешь раскрыть тему «{topic}» чуть глубже на практическом примере?",
    }
    return fallbacks[intent]


def _build_followup_question(session_data: Dict[str, object], topic: str, current_question: str, answer_text: str) -> str:
    used_questions = _used_questions(session_data)
    used_questions.add(_question_key(current_question))
    gap_intent = _infer_followup_intent(answer_text)
    results = _retrieve_followup_candidates(session_data, topic)
    prompts: List[str] = []
    for result in results:
        if not _result_matches_topic(result, topic):
            continue
        prompts.extend(_extract_followups(str(result.get("text", ""))))

    for candidate in prompts:
        sanitized = _sanitize_question(candidate)
        if not sanitized:
            continue
        if _question_key(sanitized) in used_questions:
            continue
        finalized = _finalize_question(
            session_data=session_data,
            topic=topic,
            question_kind="followup",
            candidate_question=sanitized,
            used_questions=used_questions,
            current_question=current_question,
            answer_text=answer_text,
            gap_intent=gap_intent,
        )
        if finalized:
            return finalized

    fallback = _fallback_followup_question(answer_text, topic)
    return (
        _finalize_question(
            session_data=session_data,
            topic=topic,
            question_kind="followup",
            candidate_question=fallback,
            used_questions=used_questions,
            current_question=current_question,
            answer_text=answer_text,
            gap_intent=gap_intent,
        )
        or fallback
    )


def _humanize_feedback_gap(value: str) -> str:
    labels = {
        "answer_too_short": "добавить глубину и чуть подробнее раскрыть ход мысли",
        "missing_example": "привести пример из проекта или из реальной задачи",
        "missing_tradeoff": "явно назвать компромиссы, риски или ограничения",
        "missing_result": "закончить ответ итогом и эффектом решения",
        "weak_structure": "сделать ответ более пошаговым и структурным",
    }
    normalized = value.strip()
    return labels.get(normalized, normalized.replace("_", " "))


def _build_feedback(
    answer_text: str,
    *,
    used_followup: bool,
    evaluation: Optional[Dict[str, object]] = None,
) -> str:
    from backend.services.evaluator import answer_quality

    quality = answer_quality(answer_text)
    score = int(evaluation.get("score_0_10", 0)) if evaluation else 0
    detected_gaps = [str(item) for item in evaluation.get("detected_gaps", [])] if evaluation else []

    strengths: List[str] = []
    if quality["has_structure"]:
        strengths.append("есть причинно-следственная логика")
    if quality["has_terminology"]:
        strengths.append("прозвучали корректные технические термины")
    if quality["has_example"]:
        strengths.append("есть пример или проектный контекст")
    if quality["has_tradeoff"]:
        strengths.append("ты обозначила компромиссы и ограничения")
    if quality["has_result"]:
        strengths.append("понятен итог решения и его эффект")
    if not strengths:
        strengths.append("ответ остаётся в контуре темы и не уходит в сторону")

    improvements = [_humanize_feedback_gap(item) for item in detected_gaps[:2]]
    if not improvements:
        if score >= 8:
            improvements.append("критичных пробелов в ответе не видно")
        elif quality["word_count"] < 30:
            improvements.append("добавить чуть больше деталей")
        else:
            improvements.append("можно усилить ответ конкретным примером")

    if used_followup and score >= 7:
        prefix = "После уточнения ответ стал заметно сильнее."
    elif used_followup and score >= 5:
        prefix = "После уточнения база по теме стала яснее."
    elif used_followup:
        prefix = "Даже после уточнения ответ пока остаётся поверхностным."
    elif score >= 8:
        prefix = "Можно уверенно идти дальше."
    elif score >= 5:
        prefix = "Базовое понимание видно, идём дальше."
    else:
        prefix = "Ответ частично релевантен, но неровный."

    strengths_text = "; ".join(strengths[:2])
    improvements_text = "; ".join(improvements[:2])
    return f"{prefix} Сильные стороны: {strengths_text}. Что улучшить: {improvements_text}."


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
            "next_question": _build_followup_question(session_data, current_topic, current_question, answer_text),
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
