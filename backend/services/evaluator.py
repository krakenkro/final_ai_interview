from typing import Any, Dict, List


def answer_quality(answer_text: str) -> Dict[str, Any]:
    lowered = answer_text.lower()
    word_count = len(answer_text.strip().split())

    has_example = any(marker in lowered for marker in ("example", "например", "for example", "случа", "project", "проек"))
    has_tradeoff = any(marker in lowered for marker in ("trade-off", "tradeoff", "компром", "риск", "выбор"))
    has_result = any(marker in lowered for marker in ("result", "итог", "impact", "результ", "в итоге"))
    has_structure = any(marker in lowered for marker in ("сначала", "then", "first", "second", "because", "потому", "поэтому"))
    has_terminology = any(
        marker in lowered
        for marker in (
            "props",
            "state",
            "vue",
            "nuxt",
            "typescript",
            "ssr",
            "hydration",
            "composable",
            "кэш",
            "компонент",
        )
    )

    return {
        "word_count": word_count,
        "has_example": has_example,
        "has_tradeoff": has_tradeoff,
        "has_result": has_result,
        "has_structure": has_structure,
        "has_terminology": has_terminology,
    }


def build_heuristic_evaluation(
    answer_text: str,
    *,
    current_question: str,
    current_topic: str,
    follow_up_suggestion: str,
    follow_up_threshold: int = 8,
) -> Dict[str, Any]:
    quality = answer_quality(answer_text)

    score = 0
    score += 2 if quality["word_count"] >= 45 else 1 if quality["word_count"] >= 20 else 0
    score += 2 if quality["has_example"] else 0
    score += 2 if quality["has_tradeoff"] else 0
    score += 2 if quality["has_result"] else 0
    score += 1 if quality["has_structure"] else 0
    score += 1 if quality["has_terminology"] else 0

    detected_gaps: List[str] = []
    if quality["word_count"] < 20:
        detected_gaps.append("answer_too_short")
    if not quality["has_example"]:
        detected_gaps.append("missing_example")
    if not quality["has_tradeoff"]:
        detected_gaps.append("missing_tradeoff")
    if not quality["has_result"]:
        detected_gaps.append("missing_result")
    if not quality["has_structure"]:
        detected_gaps.append("weak_structure")

    follow_up_needed = score < follow_up_threshold

    if score >= 8:
        justification = "Ответ покрывает тему достаточно глубоко, с конкретикой и признаками инженерного мышления."
    elif score >= 5:
        justification = "Ответ базово релевантен, но в нём не хватает части глубины, структуры или project-level контекста."
    else:
        justification = "Ответ пока слишком поверхностный для уверенного перехода к следующей теме."

    fallback_follow_up = (
        f'Можешь раскрыть ответ по теме "{current_topic}" глубже и добавить пример, компромиссы, риски и итог?'
        if current_topic
        else "Можешь раскрыть ответ глубже и добавить пример, компромиссы, риски и итог?"
    )

    return {
        "question": current_question,
        "topic": current_topic,
        "score_0_10": score,
        "relevance": "high" if score >= 7 else "medium" if score >= 4 else "low",
        "correctness": "heuristic",
        "completeness": "high" if score >= 7 else "medium" if score >= 4 else "low",
        "clarity": "high" if quality["has_structure"] else "medium" if quality["word_count"] >= 20 else "low",
        "terminology_precision": "high" if quality["has_terminology"] else "medium",
        "confidence_markers": "text_only_stage",
        "justification": justification,
        "detected_gaps": detected_gaps,
        "follow_up_needed": follow_up_needed,
        "suggested_follow_up": follow_up_suggestion.strip() or fallback_follow_up,
    }
