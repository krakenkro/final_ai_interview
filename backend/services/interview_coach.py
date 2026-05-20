from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]
SKILL_PATH = BASE_DIR / "skills" / "interview_coach" / "SKILL.md"


def load_skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


WEAKNESS_LABELS = {
    "answer_too_short": "Ответ получился слишком коротким и не раскрыл ход мысли.",
    "missing_example": "Не хватило конкретного примера из проекта или реального кейса.",
    "missing_tradeoff": "Не были явно названы компромиссы, риски или причины выбора решения.",
    "missing_result": "Не прозвучал итог: что получилось, как это повлияло на продукт или команду.",
    "weak_structure": "Ответу не хватило структуры: контекст, решение, trade-off, результат.",
}

TOPIC_LABELS = {
    "API integration and async flows": "интеграция с API и асинхронные сценарии",
    "Browser rendering and event loop": "рендеринг браузера и event loop",
    "JavaScript fundamentals": "JavaScript fundamentals",
    "TypeScript typing and narrowing": "TypeScript, типизация и narrowing",
    "React component model": "модель React-компонентов",
    "State management and data flow": "state management и data flow",
    "Performance and optimization basics": "performance и оптимизация",
    "Testing fundamentals": "тестирование frontend-приложений",
    "Resume-based project deep dive": "разбор проекта из резюме",
    "ownership": "ownership и личная ответственность",
    "conflict resolution": "разрешение конфликтов",
    "prioritization": "приоритизация и trade-offs",
    "failure / lessons learned": "ошибки и извлечённые уроки",
    "communication of trade-offs": "объяснение trade-offs",
    "incident handling / debugging stories": "разбор инцидентов и debugging stories",
}


def _humanize_weakness(value: str) -> str:
    normalized = value.strip()
    return WEAKNESS_LABELS.get(normalized, normalized.replace("_", " "))


def _humanize_topic(value: str) -> str:
    normalized = value.strip()
    return TOPIC_LABELS.get(normalized, normalized)


def _normalize_drill(value: str) -> str:
    drill = value.strip()
    if not drill:
        return ""
    if drill.startswith("Follow-up:"):
        drill = drill.replace("Follow-up:", "", 1).strip()
    if "Свяжи это с вопросом:" in drill:
        prompt, question = drill.split("Свяжи это с вопросом:", 1)
        prompt = prompt.strip()
        question = question.strip().rstrip("?")
        if prompt.lower() == "request-response flow":
            if question.lower().startswith("как "):
                question = question[4:].strip()
            return f"Как request-response flow связан с тем, как {question} под капотом?"
        return f'Раскрой аспект "{prompt}" и свяжи его с вопросом: "{question}?"'
    return drill


def _build_improvements(weaknesses: List[str], improvements: List[str]) -> List[str]:
    actions: List[str] = []
    weakness_set = set(weaknesses)

    if "missing_example" in weakness_set:
        actions.append("Добавляй к ответу один конкретный пример из проекта, а не только определение.")
    if "missing_tradeoff" in weakness_set:
        actions.append("Явно проговаривай компромиссы: почему выбрала именно это решение и чем пожертвовала.")
    if "missing_result" in weakness_set:
        actions.append("Заканчивай ответ итогом: что получилось, какой был эффект и как это измерялось.")
    if "weak_structure" in weakness_set or "answer_too_short" in weakness_set:
        actions.append("Строй ответ по схеме: контекст, решение, trade-off, результат.")

    for topic in improvements:
        label = _humanize_topic(topic)
        candidate = f"Отдельно повтори тему: {label}."
        if candidate not in actions:
            actions.append(candidate)

    return actions[:4]


def _build_drills(drills: List[str]) -> List[str]:
    normalized = [_normalize_drill(item) for item in drills]
    normalized = [item for item in normalized if item]
    if not normalized:
        return ["Прогони вслух 2-3 ответа по схеме: контекст, решение, trade-off, результат."]

    payload: List[str] = []
    for item in normalized[:4]:
        if item.endswith("?"):
            payload.append(f'Потренируй вслух ответ на вопрос: "{item}"')
        else:
            payload.append(f'Отдельно раскрой аспект: "{item}"')
    return payload


def build_coaching_report(
    *,
    strengths: List[str],
    weaknesses: List[str],
    improvements: List[str],
    drills: List[str],
) -> Dict[str, Any]:
    good = [item.strip() for item in strengths if item.strip()]
    weak = [_humanize_weakness(item) for item in weaknesses if item.strip()]
    improvement_plan = _build_improvements(weaknesses, improvements)
    recommended_drills = _build_drills(drills)

    return {
        "skill_name": "Interview Coach",
        "skill_path": str(SKILL_PATH.relative_to(BASE_DIR)),
        "skill_loaded": True,
        "what_was_good": good[:4] or ["Есть базовая тематическая релевантность по ходу интервью."],
        "what_was_weak": weak[:4],
        "how_to_improve": improvement_plan,
        "recommended_drills": recommended_drills,
        "raw_skill_excerpt": load_skill_text()[:400],
    }
