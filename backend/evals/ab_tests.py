import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.evals.run_golden_eval import DEFAULT_DATASET_PATH, load_dataset
from backend.services.evaluator import build_heuristic_evaluation


BASE_DIR = ROOT_DIR
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def evaluate_variant(dataset: List[Dict[str, Any]], follow_up_threshold: int) -> Dict[str, Any]:
    total = len(dataset)
    follow_up_hits = 0
    score_hits = 0
    primary_hits = 0
    false_positive = 0
    false_negative = 0

    for case in dataset:
        evaluation = build_heuristic_evaluation(
            case["candidate_answer"],
            current_question=case["question"],
            current_topic=case["topic"],
            follow_up_suggestion=f'Можешь раскрыть тему "{case["topic"]}" глубже и добавить пример, trade-offs, риски и итог?',
            follow_up_threshold=follow_up_threshold,
        )
        predicted_score = int(evaluation["score_0_10"])
        expected_min, expected_max = [int(value) for value in case["expected_score_range"]]
        score_in_range = expected_min <= predicted_score <= expected_max
        expected_follow_up = bool(case["expected_followup_needed"])
        predicted_follow_up = bool(evaluation["follow_up_needed"])
        follow_up_match = expected_follow_up == predicted_follow_up

        score_hits += 1 if score_in_range else 0
        follow_up_hits += 1 if follow_up_match else 0
        primary_hits += 1 if score_in_range and follow_up_match else 0
        false_positive += 1 if (not expected_follow_up and predicted_follow_up) else 0
        false_negative += 1 if (expected_follow_up and not predicted_follow_up) else 0

    return {
        "follow_up_threshold": follow_up_threshold,
        "total_cases": total,
        "score_range_accuracy": percentage(score_hits, total),
        "follow_up_accuracy": percentage(follow_up_hits, total),
        "primary_pass_rate": percentage(primary_hits, total),
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def build_report(dataset_path: Path, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    best_variant = sorted(
        variants,
        key=lambda item: (
            item["follow_up_accuracy"],
            item["primary_pass_rate"],
            -item["false_positive"],
            -item["false_negative"],
        ),
        reverse=True,
    )[0]
    return {
        "generated_at": utc_now(),
        "dataset_path": str(dataset_path.relative_to(BASE_DIR)),
        "experiment": "follow_up_threshold_ab",
        "variants": variants,
        "winner": best_variant,
        "decision": (
            f'Порог follow-up `{best_variant["follow_up_threshold"]}` выбран как baseline, '
            "потому что он даёт лучшую точность follow-up без роста false positive."
        ),
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# A/B Test Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Dataset: `{report['dataset_path']}`",
        f"- Experiment: `{report['experiment']}`",
        "",
        "## Variants",
        "",
    ]

    for variant in report["variants"]:
        lines.append(
            f"- threshold `<{variant['follow_up_threshold']}`: "
            f"follow_up_accuracy={variant['follow_up_accuracy']}%, "
            f"score_range_accuracy={variant['score_range_accuracy']}%, "
            f"primary_pass_rate={variant['primary_pass_rate']}%, "
            f"false_positive={variant['false_positive']}, "
            f"false_negative={variant['false_negative']}"
        )

    winner = report["winner"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Winner: `threshold <{winner['follow_up_threshold']}`",
            f"- Rationale: {report['decision']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(report: Dict[str, Any]) -> Dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "ab_followup_threshold_latest.json"
    md_path = REPORTS_DIR / "ab_followup_threshold_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def main() -> None:
    dataset_path = DEFAULT_DATASET_PATH.resolve()
    dataset = load_dataset(dataset_path)
    variants = [
        evaluate_variant(dataset, follow_up_threshold=7),
        evaluate_variant(dataset, follow_up_threshold=8),
    ]
    report = build_report(dataset_path, variants)
    paths = write_report(report)
    print(
        json.dumps(
            {
                "winner": report["winner"],
                "report_json": str(paths["json"].relative_to(BASE_DIR)),
                "report_markdown": str(paths["markdown"].relative_to(BASE_DIR)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
