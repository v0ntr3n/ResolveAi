import json
from pathlib import Path

from app.evals.runner import summarize_results


def test_eval_queries_file_has_bilingual_coverage():
    path = Path("data/evals/test_queries.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert len(payload["cases"]) >= 20
    languages = {case["language"] for case in payload["cases"]}
    intents = {case["expected_intent"] for case in payload["cases"]}

    assert {"en", "vi"} <= languages
    assert {"order_status", "refund", "address_change", "policy_question"} <= intents


def test_summarize_results_counts_resolution_and_escalation_rates():
    summary = summarize_results(
        [
            {"resolved": True, "requires_human": False, "intent_match": True},
            {"resolved": False, "requires_human": True, "intent_match": True},
            {"resolved": True, "requires_human": False, "intent_match": False},
        ]
    )

    assert summary["total_cases"] == 3
    assert summary["resolved_count"] == 2
    assert summary["escalation_count"] == 1
    assert summary["intent_match_count"] == 2
