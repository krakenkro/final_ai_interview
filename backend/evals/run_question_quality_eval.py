import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[2]
EVALS_DIR = Path(__file__).resolve().parent
REPORTS_DIR = EVALS_DIR / "reports"
DEFAULT_DATASET_PATH = EVALS_DIR / "question_quality_golden_dataset.jsonl"

REQUIRED_TOPICS = {
    "Vue 3 component model",
    "Vue reactivity and refs",
    "Nuxt 3 fundamentals",
    "Nuxt routing and data fetching",
    "TypeScript in frontend apps",
    "API integration and async flows",
    "browser rendering and event loop",
    "performance and optimization basics",
    "resume-based project deep dive",
    "ownership",
    "conflict resolution",
    "prioritization",
    "failure / lessons learned",
}

REQUIRED_NEGATIVE_PATTERN_TAGS = {
    "phrase_loop",
    "abstract_label",
    "too_long",
    "mixed_ru_en",
    "no_new_axis",
    "string_mashup",
}

ALLOWED_CASE_TYPES = {"main_question", "follow_up"}
ALLOWED_ACTIONS = {"accept", "rewrite", "reject"}
ALLOWED_INTERVIEW_TYPES = {"Technical Core", "Mixed", "Behavioural"}
ALLOWED_FOLLOWUP_INTENTS = {
    "ask_example",
    "ask_tradeoff",
    "ask_edge_case",
    "ask_debugging",
    "deepen_mechanism",
    "probe_specificity",
    "probe_reflection",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_case(case: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    case_type = case.get("case_type")
    expected_action = case.get("expected_action")

    common_string_fields = [
        "id",
        "role",
        "interview_type",
        "topic",
        "source_context_type",
        "expected_question_style",
        "expected_language",
        "notes_for_human_reviewer",
    ]
    for field in common_string_fields:
        if not _non_empty_string(case.get(field)):
            errors.append(f"{field}: must be a non-empty string")

    if case_type not in ALLOWED_CASE_TYPES:
        errors.append(f"case_type: must be one of {sorted(ALLOWED_CASE_TYPES)}")
    if expected_action not in ALLOWED_ACTIONS:
        errors.append(f"expected_action: must be one of {sorted(ALLOWED_ACTIONS)}")
    if case.get("role") != "Frontend Developer":
        errors.append('role: must be "Frontend Developer"')
    if case.get("interview_type") not in ALLOWED_INTERVIEW_TYPES:
        errors.append(f"interview_type: must be one of {sorted(ALLOWED_INTERVIEW_TYPES)}")
    if case.get("topic") not in REQUIRED_TOPICS:
        errors.append("topic: must belong to the approved Vue/Nuxt + behavioural baseline")
    if case.get("expected_language") != "ru":
        errors.append('expected_language: must be "ru"')
    if case.get("should_sound_like_interviewer") is not True:
        errors.append("should_sound_like_interviewer: must be true")

    max_length_chars = case.get("max_length_chars")
    if not isinstance(max_length_chars, int) or max_length_chars < 60 or max_length_chars > 220:
        errors.append("max_length_chars: must be an int between 60 and 220")

    for field in ("must_include_any", "must_not_include_any", "negative_pattern_tags"):
        if not _string_list(case.get(field)):
            errors.append(f"{field}: must be a list of strings")

    if expected_action in {"rewrite", "reject"} and not case.get("negative_pattern_tags"):
        errors.append("negative_pattern_tags: rewrite/reject cases must list at least one negative pattern")

    if case_type == "main_question":
        if not _non_empty_string(case.get("input_candidate_question")):
            errors.append("input_candidate_question: must be a non-empty string for main_question")
    elif case_type == "follow_up":
        followup_fields = [
            "gap_type",
            "current_question",
            "previous_answer_summary",
            "input_followup_candidate",
            "expected_followup_intent",
        ]
        for field in followup_fields:
            if not _non_empty_string(case.get(field)):
                errors.append(f"{field}: must be a non-empty string for follow_up")
        if case.get("expected_followup_intent") not in ALLOWED_FOLLOWUP_INTENTS:
            errors.append(
                f"expected_followup_intent: must be one of {sorted(ALLOWED_FOLLOWUP_INTENTS)}"
            )

    return errors


def build_report(dataset_path: Path, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    validations = []
    topic_counter: Counter[str] = Counter()
    case_type_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    interview_type_counter: Counter[str] = Counter()
    negative_tag_counter: Counter[str] = Counter()
    followup_intent_counter: Counter[str] = Counter()

    for case in dataset:
        errors = validate_case(case)
        validations.append({"id": case.get("id", "unknown"), "errors": errors})
        topic_counter[str(case.get("topic", "unknown"))] += 1
        case_type_counter[str(case.get("case_type", "unknown"))] += 1
        action_counter[str(case.get("expected_action", "unknown"))] += 1
        interview_type_counter[str(case.get("interview_type", "unknown"))] += 1
        for tag in case.get("negative_pattern_tags", []):
            negative_tag_counter[str(tag)] += 1
        if case.get("case_type") == "follow_up" and _non_empty_string(case.get("expected_followup_intent")):
            followup_intent_counter[str(case["expected_followup_intent"])] += 1

    failing = [item for item in validations if item["errors"]]
    schema_valid_cases = len(dataset) - len(failing)
    missing_topics = sorted(REQUIRED_TOPICS - set(topic_counter))
    missing_negative_tags = sorted(REQUIRED_NEGATIVE_PATTERN_TAGS - set(negative_tag_counter))
    total_cases = len(dataset)
    within_target_size = 24 <= total_cases <= 30

    return {
        "generated_at": utc_now(),
        "dataset_path": str(dataset_path.relative_to(ROOT_DIR)),
        "summary": {
            "total_cases": total_cases,
            "schema_valid_rate": percentage(schema_valid_cases, total_cases),
            "within_target_size": within_target_size,
            "topic_coverage_complete": not missing_topics,
            "negative_pattern_coverage_complete": not missing_negative_tags,
            "main_question_cases": case_type_counter.get("main_question", 0),
            "follow_up_cases": case_type_counter.get("follow_up", 0),
        },
        "counts": {
            "by_case_type": dict(case_type_counter),
            "by_expected_action": dict(action_counter),
            "by_interview_type": dict(interview_type_counter),
            "by_topic": dict(sorted(topic_counter.items())),
            "by_negative_pattern_tag": dict(sorted(negative_tag_counter.items())),
            "by_followup_intent": dict(sorted(followup_intent_counter.items())),
        },
        "missing_topics": missing_topics,
        "missing_negative_pattern_tags": missing_negative_tags,
        "schema_failures": failing,
        "ready_for_data_rewrite": within_target_size and not missing_topics and not missing_negative_tags and not failing,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Question Quality Dataset Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Dataset: `{report['dataset_path']}`",
        f"- Total cases: `{summary['total_cases']}`",
        f"- Schema valid rate: `{summary['schema_valid_rate']}%`",
        f"- Main question cases: `{summary['main_question_cases']}`",
        f"- Follow-up cases: `{summary['follow_up_cases']}`",
        f"- Within target size 24-30: `{summary['within_target_size']}`",
        f"- Topic coverage complete: `{summary['topic_coverage_complete']}`",
        f"- Negative pattern coverage complete: `{summary['negative_pattern_coverage_complete']}`",
        f"- Ready for data rewrite: `{report['ready_for_data_rewrite']}`",
        "",
        "## Negative Pattern Coverage",
        "",
    ]

    for tag, count in report["counts"]["by_negative_pattern_tag"].items():
        lines.append(f"- `{tag}`: `{count}`")

    if report["missing_negative_pattern_tags"]:
        lines.extend(
            [
                "",
                "## Missing Negative Pattern Tags",
                "",
            ]
        )
        for tag in report["missing_negative_pattern_tags"]:
            lines.append(f"- `{tag}`")

    lines.extend(
        [
            "",
            "## Topic Coverage",
            "",
        ]
    )
    for topic, count in report["counts"]["by_topic"].items():
        lines.append(f"- `{topic}`: `{count}`")

    if report["missing_topics"]:
        lines.extend(
            [
                "",
                "## Missing Topics",
                "",
            ]
        )
        for topic in report["missing_topics"]:
            lines.append(f"- `{topic}`")

    lines.extend(
        [
            "",
            "## Case Distribution",
            "",
        ]
    )
    for case_type, count in report["counts"]["by_case_type"].items():
        lines.append(f"- `{case_type}`: `{count}`")
    for action, count in report["counts"]["by_expected_action"].items():
        lines.append(f"- action `{action}`: `{count}`")

    if report["schema_failures"]:
        lines.extend(
            [
                "",
                "## Schema Failures",
                "",
            ]
        )
        for item in report["schema_failures"]:
            lines.append(f"- `{item['id']}`: {', '.join(item['errors'])}")

    return "\n".join(lines) + "\n"


def write_report(report: Dict[str, Any]) -> Dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "question_quality_dataset_latest.json"
    md_path = REPORTS_DIR / "question_quality_dataset_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    dataset = load_dataset(dataset_path)
    report = build_report(dataset_path, dataset)
    paths = write_report(report)
    print(
        json.dumps(
            {
                "summary": report["summary"],
                "missing_topics": report["missing_topics"],
                "missing_negative_pattern_tags": report["missing_negative_pattern_tags"],
                "ready_for_data_rewrite": report["ready_for_data_rewrite"],
                "report_json": str(paths["json"].relative_to(ROOT_DIR)),
                "report_markdown": str(paths["markdown"].relative_to(ROOT_DIR)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
