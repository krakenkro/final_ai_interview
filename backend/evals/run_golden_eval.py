import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.evaluator import build_heuristic_evaluation


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = EVALS_DIR / "answer_evaluation_golden_dataset.jsonl"
REPORTS_DIR = EVALS_DIR / "reports"
BASE_DIR = ROOT_DIR


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


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)


def _default_follow_up(question: str, topic: str) -> str:
    if topic:
        return f'Можешь раскрыть тему "{topic}" глубже и добавить пример, компромиссы, риски и итог?'
    return f"Можешь раскрыть ответ на вопрос '{question}' глубже и добавить пример, компромиссы, риски и итог?"


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    evaluation = build_heuristic_evaluation(
        case["candidate_answer"],
        current_question=case["question"],
        current_topic=case["topic"],
        follow_up_suggestion=_default_follow_up(case["question"], case["topic"]),
    )

    predicted_score = int(evaluation["score_0_10"])
    expected_range = case["expected_score_range"]
    expected_min = int(expected_range[0])
    expected_max = int(expected_range[1])
    score_in_range = expected_min <= predicted_score <= expected_max
    score_distance = 0 if score_in_range else expected_min - predicted_score if predicted_score < expected_min else predicted_score - expected_max

    predicted_follow_up = bool(evaluation["follow_up_needed"])
    expected_follow_up = bool(case["expected_followup_needed"])
    follow_up_match = predicted_follow_up == expected_follow_up

    predicted_gaps = list(evaluation.get("detected_gaps", []))
    expected_gaps = list(case.get("expected_gaps", []))
    predicted_gap_set = set(predicted_gaps)
    expected_gap_set = set(expected_gaps)
    gap_overlap = sorted(predicted_gap_set & expected_gap_set)
    gap_exact_match = predicted_gap_set == expected_gap_set
    gap_recall = 1.0 if not expected_gap_set and not predicted_gap_set else 0.0 if not expected_gap_set else ratio(len(gap_overlap), len(expected_gap_set))
    gap_precision = 1.0 if not predicted_gap_set and not expected_gap_set else 0.0 if not predicted_gap_set else ratio(len(gap_overlap), len(predicted_gap_set))

    primary_pass = score_in_range and follow_up_match

    return {
        "id": case["id"],
        "role": case["role"],
        "seniority": case["seniority"],
        "interview_type": case["interview_type"],
        "topic": case["topic"],
        "question": case["question"],
        "answer_quality_label": case.get("answer_quality_label", ""),
        "expected_score_range": [expected_min, expected_max],
        "predicted_score_0_10": predicted_score,
        "score_in_range": score_in_range,
        "score_distance": score_distance,
        "expected_followup_needed": expected_follow_up,
        "predicted_followup_needed": predicted_follow_up,
        "follow_up_match": follow_up_match,
        "expected_gaps": expected_gaps,
        "predicted_gaps": predicted_gaps,
        "gap_overlap": gap_overlap,
        "gap_exact_match": gap_exact_match,
        "gap_recall": gap_recall,
        "gap_precision": gap_precision,
        "primary_pass": primary_pass,
        "evaluation": evaluation,
    }


def _build_breakdown(cases: List[Dict[str, Any]], field: str) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[str(case.get(field, "unknown"))].append(case)

    breakdown: Dict[str, Dict[str, Any]] = {}
    for key, group in sorted(grouped.items()):
        total = len(group)
        score_hits = sum(1 for item in group if item["score_in_range"])
        followup_hits = sum(1 for item in group if item["follow_up_match"])
        primary_hits = sum(1 for item in group if item["primary_pass"])
        gap_exact_hits = sum(1 for item in group if item["gap_exact_match"])
        avg_gap_recall = round(sum(float(item["gap_recall"]) for item in group) / total, 4) if total else 0.0
        avg_gap_precision = round(sum(float(item["gap_precision"]) for item in group) / total, 4) if total else 0.0
        avg_score = round(sum(int(item["predicted_score_0_10"]) for item in group) / total, 2) if total else 0.0
        breakdown[key] = {
            "total_cases": total,
            "score_range_accuracy": percentage(score_hits, total),
            "follow_up_accuracy": percentage(followup_hits, total),
            "primary_pass_rate": percentage(primary_hits, total),
            "gap_exact_match_rate": percentage(gap_exact_hits, total),
            "avg_gap_recall": avg_gap_recall,
            "avg_gap_precision": avg_gap_precision,
            "avg_predicted_score": avg_score,
        }
    return breakdown


def build_report(dataset_path: Path, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(cases)
    score_hits = sum(1 for item in cases if item["score_in_range"])
    followup_hits = sum(1 for item in cases if item["follow_up_match"])
    primary_hits = sum(1 for item in cases if item["primary_pass"])
    gap_exact_hits = sum(1 for item in cases if item["gap_exact_match"])
    avg_gap_recall = round(sum(float(item["gap_recall"]) for item in cases) / total, 4) if total else 0.0
    avg_gap_precision = round(sum(float(item["gap_precision"]) for item in cases) / total, 4) if total else 0.0
    avg_score_distance = round(sum(int(item["score_distance"]) for item in cases) / total, 4) if total else 0.0
    avg_predicted_score = round(sum(int(item["predicted_score_0_10"]) for item in cases) / total, 2) if total else 0.0

    followup_true_positive = sum(1 for item in cases if item["expected_followup_needed"] and item["predicted_followup_needed"])
    followup_true_negative = sum(1 for item in cases if not item["expected_followup_needed"] and not item["predicted_followup_needed"])
    followup_false_positive = sum(1 for item in cases if not item["expected_followup_needed"] and item["predicted_followup_needed"])
    followup_false_negative = sum(1 for item in cases if item["expected_followup_needed"] and not item["predicted_followup_needed"])

    failing_cases = [item for item in cases if not item["primary_pass"]]

    return {
        "generated_at": utc_now(),
        "dataset_path": str(dataset_path.relative_to(BASE_DIR)),
        "total_cases": total,
        "summary": {
            "score_range_accuracy": percentage(score_hits, total),
            "follow_up_accuracy": percentage(followup_hits, total),
            "primary_pass_rate": percentage(primary_hits, total),
            "gap_exact_match_rate": percentage(gap_exact_hits, total),
            "avg_gap_recall": avg_gap_recall,
            "avg_gap_precision": avg_gap_precision,
            "avg_score_distance": avg_score_distance,
            "avg_predicted_score": avg_predicted_score,
        },
        "follow_up_confusion": {
            "true_positive": followup_true_positive,
            "true_negative": followup_true_negative,
            "false_positive": followup_false_positive,
            "false_negative": followup_false_negative,
        },
        "breakdowns": {
            "by_role": _build_breakdown(cases, "role"),
            "by_interview_type": _build_breakdown(cases, "interview_type"),
            "by_seniority": _build_breakdown(cases, "seniority"),
            "by_answer_quality_label": _build_breakdown(cases, "answer_quality_label"),
        },
        "failing_case_ids": [item["id"] for item in failing_cases],
        "cases": cases,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    summary = report["summary"]
    confusion = report["follow_up_confusion"]
    lines = [
        "# Golden Dataset Eval Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Dataset: `{report['dataset_path']}`",
        f"- Total cases: `{report['total_cases']}`",
        f"- Score range accuracy: `{summary['score_range_accuracy']}%`",
        f"- Follow-up accuracy: `{summary['follow_up_accuracy']}%`",
        f"- Primary pass rate: `{summary['primary_pass_rate']}%`",
        f"- Gap exact match rate: `{summary['gap_exact_match_rate']}%`",
        f"- Avg gap recall: `{summary['avg_gap_recall']}`",
        f"- Avg gap precision: `{summary['avg_gap_precision']}`",
        f"- Avg score distance: `{summary['avg_score_distance']}`",
        f"- Avg predicted score: `{summary['avg_predicted_score']}`",
        "",
        "## Follow-up Confusion",
        "",
        f"- true_positive: `{confusion['true_positive']}`",
        f"- true_negative: `{confusion['true_negative']}`",
        f"- false_positive: `{confusion['false_positive']}`",
        f"- false_negative: `{confusion['false_negative']}`",
        "",
        "## Breakdowns",
        "",
    ]

    for section, values in report["breakdowns"].items():
        lines.append(f"### {section}")
        lines.append("")
        for key, metrics in values.items():
            lines.append(
                f"- `{key}`: score_range_accuracy={metrics['score_range_accuracy']}%, "
                f"follow_up_accuracy={metrics['follow_up_accuracy']}%, "
                f"primary_pass_rate={metrics['primary_pass_rate']}%, "
                f"gap_exact_match_rate={metrics['gap_exact_match_rate']}%, "
                f"avg_gap_recall={metrics['avg_gap_recall']}, "
                f"avg_predicted_score={metrics['avg_predicted_score']}"
            )
        lines.append("")

    lines.extend(["## Failed Cases", ""])
    failed = [case for case in report["cases"] if not case["primary_pass"]]
    if not failed:
        lines.append("- none")
    else:
        for case in failed:
            lines.append(
                f"- `{case['id']}`: score={case['predicted_score_0_10']} expected={case['expected_score_range']}, "
                f"follow_up={case['predicted_followup_needed']} expected_follow_up={case['expected_followup_needed']}"
            )

    return "\n".join(lines) + "\n"


def write_report(report: Dict[str, Any]) -> Dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "golden_eval_latest.json"
    md_path = REPORTS_DIR / "golden_eval_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluator checks over the local golden dataset.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to the JSONL dataset with golden evaluation cases.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    dataset = load_dataset(dataset_path)
    cases = [evaluate_case(case) for case in dataset]
    report = build_report(dataset_path, cases)
    paths = write_report(report)

    payload = {
        "summary": report["summary"],
        "follow_up_confusion": report["follow_up_confusion"],
        "report_json": str(paths["json"].relative_to(BASE_DIR)),
        "report_markdown": str(paths["markdown"].relative_to(BASE_DIR)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
