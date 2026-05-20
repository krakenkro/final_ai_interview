import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.services.rag import retrieve_context
from backend.services.rag_ingestion import BASE_DIR


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = EVALS_DIR / "rag_queries.jsonl"
REPORTS_DIR = EVALS_DIR / "reports"


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


def all_results_match_filter(results: List[Dict[str, Any]], filters: Dict[str, Any]) -> bool:
    if not results:
        return False

    role = filters.get("role")
    seniority = filters.get("seniority")
    interview_type = filters.get("interview_type")
    document_types = {value.lower() for value in filters.get("document_types", [])}

    for result in results:
        if role and result.get("role") != role:
            return False
        if seniority and seniority not in result.get("seniority", []):
            return False
        if interview_type and interview_type not in result.get("interview_type", []):
            return False
        if document_types and str(result.get("document_type", "")).lower() not in document_types:
            return False
    return True


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    filters = case.get("filters", {})
    top_k = int(case.get("top_k", 5))
    results = retrieve_context(
        case["query"],
        top_k=top_k,
        role=filters.get("role"),
        seniority=filters.get("seniority"),
        interview_type=filters.get("interview_type"),
        document_types=filters.get("document_types"),
        layer=filters.get("layer", "processed"),
    )

    observed_topics = [str(item.get("topic", "")) for item in results if "topic" in item]
    observed_document_types = [str(item.get("document_type", "")) for item in results if "document_type" in item]
    observed_backend = results[0].get("retrieval_backend") if results else None

    expected_topics = set(case.get("expect_any_topics", []))
    expected_document_types = set(case.get("expect_any_document_types", []))

    topic_hit = any(topic in expected_topics for topic in observed_topics)
    document_type_hit = any(document_type in expected_document_types for document_type in observed_document_types)
    backend_ok = not case.get("expected_backend") or observed_backend == case.get("expected_backend")
    filters_ok = all_results_match_filter(results, filters)

    passed = bool(results) and topic_hit and document_type_hit and backend_ok and filters_ok

    return {
        "case_id": case["case_id"],
        "query": case["query"],
        "notes": case.get("notes", ""),
        "filters": filters,
        "expected_backend": case.get("expected_backend"),
        "expected_topics": sorted(expected_topics),
        "expected_document_types": sorted(expected_document_types),
        "observed_backend": observed_backend,
        "observed_topics": observed_topics,
        "observed_document_types": observed_document_types,
        "result_count": len(results),
        "topic_hit": topic_hit,
        "document_type_hit": document_type_hit,
        "backend_ok": backend_ok,
        "filters_ok": filters_ok,
        "passed": passed,
        "results": results,
    }


def percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def build_report(dataset_path: Path, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(cases)
    topic_hits = sum(1 for case in cases if case["topic_hit"])
    document_type_hits = sum(1 for case in cases if case["document_type_hit"])
    backend_hits = sum(1 for case in cases if case["backend_ok"])
    filter_hits = sum(1 for case in cases if case["filters_ok"])
    passed = sum(1 for case in cases if case["passed"])

    backends = Counter(case.get("observed_backend") or "unknown" for case in cases)
    failing_cases = [case for case in cases if not case["passed"]]

    return {
        "generated_at": utc_now(),
        "dataset_path": str(dataset_path.relative_to(BASE_DIR)),
        "total_cases": total,
        "summary": {
            "passed_cases": passed,
            "failed_cases": total - passed,
            "pass_rate": percentage(passed, total),
            "topic_hit_rate": percentage(topic_hits, total),
            "document_type_hit_rate": percentage(document_type_hits, total),
            "backend_expected_rate": percentage(backend_hits, total),
            "filters_ok_rate": percentage(filter_hits, total),
        },
        "observed_backends": dict(backends),
        "cases": cases,
        "failing_case_ids": [case["case_id"] for case in failing_cases],
    }


def render_markdown(report: Dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# RAG Eval Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Dataset: `{report['dataset_path']}`",
        f"- Total cases: `{report['total_cases']}`",
        f"- Pass rate: `{summary['pass_rate']}%`",
        f"- Topic hit rate: `{summary['topic_hit_rate']}%`",
        f"- Document type hit rate: `{summary['document_type_hit_rate']}%`",
        f"- Backend expected rate: `{summary['backend_expected_rate']}%`",
        f"- Filters OK rate: `{summary['filters_ok_rate']}%`",
        "",
        "## Observed Backends",
        "",
    ]

    for backend, count in sorted(report["observed_backends"].items()):
        lines.append(f"- `{backend}`: {count}")

    lines.extend(["", "## Failed Cases", ""])
    failed = [case for case in report["cases"] if not case["passed"]]
    if not failed:
        lines.append("- none")
    else:
        for case in failed:
            lines.append(
                f"- `{case['case_id']}`: topic_hit={case['topic_hit']}, "
                f"document_type_hit={case['document_type_hit']}, "
                f"backend_ok={case['backend_ok']}, filters_ok={case['filters_ok']}"
            )

    return "\n".join(lines) + "\n"


def write_report(report: Dict[str, Any]) -> Dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "rag_eval_latest.json"
    md_path = REPORTS_DIR / "rag_eval_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run retrieval evaluation over the local RAG dataset.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to the JSONL dataset with retrieval evaluation cases.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    dataset = load_dataset(dataset_path)
    cases = [evaluate_case(case) for case in dataset]
    report = build_report(dataset_path, cases)
    paths = write_report(report)

    payload = {
        "summary": report["summary"],
        "observed_backends": report["observed_backends"],
        "report_json": str(paths["json"].relative_to(BASE_DIR)),
        "report_markdown": str(paths["markdown"].relative_to(BASE_DIR)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
