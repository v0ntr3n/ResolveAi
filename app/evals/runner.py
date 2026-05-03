from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["cases"]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(results)
    resolved_count = sum(1 for row in results if row["resolved"])
    escalation_count = sum(1 for row in results if row["requires_human"])
    intent_match_count = sum(1 for row in results if row["intent_match"])
    return {
        "total_cases": total_cases,
        "resolved_count": resolved_count,
        "escalation_count": escalation_count,
        "intent_match_count": intent_match_count,
        "resolution_rate": round(resolved_count / total_cases, 3) if total_cases else 0.0,
        "escalation_rate": round(escalation_count / total_cases, 3) if total_cases else 0.0,
        "intent_accuracy": round(intent_match_count / total_cases, 3) if total_cases else 0.0,
    }


def run_eval_suite(
    cases_path: Path | None = None,
    report_path: Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    resolved_cases_path = cases_path or Path("data/evals/test_queries.json")
    resolved_report_path = report_path or Path("data/evals/latest_report.json")

    cases = load_eval_cases(resolved_cases_path)
    if limit is not None:
        cases = cases[:limit]

    results: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for case in cases:
            response = client.post("/chat", json={"message": case["prompt"]})
            response.raise_for_status()
            payload = response.json()
            results.append(
                {
                    "id": case["id"],
                    "language": case["language"],
                    "prompt": case["prompt"],
                    "expected_intent": case["expected_intent"],
                    "actual_intent": payload["intent"],
                    "intent_match": payload["intent"] == case["expected_intent"],
                    "resolved": payload["resolved"],
                    "requires_human": payload["requires_human"],
                    "tool_used": payload["tool_used"],
                    "response": payload["response"],
                }
            )

    summary = summarize_results(results)
    report = {"summary": summary, "results": results}
    resolved_report_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    report = run_eval_suite()
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
