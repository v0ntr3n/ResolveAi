import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.evals.runner import load_eval_cases, run_eval_suite


def test_load_eval_cases_reads_cases_file():
    cases = load_eval_cases(Path("data/evals/test_queries.json"))

    assert len(cases) >= 20
    assert all("prompt" in case for case in cases)


@patch("app.services.retrieval.OpenAIEmbeddings")
def test_run_eval_suite_writes_summary_report(mock_embeddings, tmp_path):
    """Test eval suite runs and writes report without requiring API keys."""
    # Mock embeddings to avoid API calls
    mock_instance = MagicMock()
    mock_instance.embed_query.return_value = [0.1] * 1536
    mock_embeddings.return_value = mock_instance
    
    report_path = tmp_path / "eval_report.json"
    result = run_eval_suite(report_path=report_path, limit=3)

    assert result["summary"]["total_cases"] == 3
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert "summary" in payload
    assert len(payload["results"]) == 3
