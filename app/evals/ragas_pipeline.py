"""RAGAS evaluation pipeline for automated RAG quality assessment."""

import json
from datetime import datetime, UTC
from pathlib import Path

from app.agent.graph import build_support_graph
from app.data.db import get_session_factory
from app.evals.ragas_eval import RAGASEvaluator
from app.services.retrieval import retrieve_policy_context


def run_ragas_evaluation(limit: int | None = None):
    """Run complete RAGAS evaluation pipeline.

    Args:
        limit: Optional limit on number of test cases to evaluate.

    Returns:
        Evaluation report dictionary.
    """
    # Load test cases
    test_cases_path = Path("data/evals/ragas_test_cases.json")

    if not test_cases_path.exists():
        print(f"ERROR: RAGAS test cases not found at {test_cases_path}")
        return None

    with open(test_cases_path) as f:
        test_cases = json.load(f)

    if limit:
        test_cases = test_cases[:limit]

    print(f"Loaded {len(test_cases)} test cases for evaluation")

    # Build graph
    graph = build_support_graph()
    session_factory = get_session_factory()

    # Generate responses
    evaluation_cases = []

    for case in test_cases:
        print(f"Processing test case {case['id']}: {case['query'][:50]}...")

        # Execute RAG pipeline
        with session_factory() as session:
            result = graph.invoke({
                "message": case["query"],
                "conversation_id": f"eval-{case['id']}",
                "db_session": session,
            })

        # Retrieve contexts
        contexts = []
        if result.get("intent") == "policy_question":
            policy_context = retrieve_policy_context(case["query"])
            contexts = [policy_context["content"]]

        evaluation_cases.append({
            "id": case["id"],
            "query": case["query"],
            "generated_answer": result["response"],
            "retrieved_contexts": contexts,
            "expected_answer": case["expected_answer"],
            "intent": result["intent"],
        })

    # Run RAGAS evaluation
    print("Running RAGAS evaluation...")
    evaluator = RAGASEvaluator()
    metrics = evaluator.evaluate_rag(evaluation_cases)

    # Generate report
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": metrics,
        "cases": evaluation_cases,
        "summary": {
            "total_cases": len(evaluation_cases),
            "avg_faithfulness": metrics["faithfulness"],
            "avg_relevancy": metrics["answer_relevancy"],
            "avg_context_precision": metrics["context_precision"],
            "avg_context_recall": metrics["context_recall"],
            "overall_score": metrics["overall_score"],
        },
    }

    # Save report
    report_path = Path("data/evals/ragas_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nEvaluation complete!")
    print(f"Overall Score: {metrics['overall_score']:.3f}")
    print(f"Faithfulness: {metrics['faithfulness']:.3f}")
    print(f"Answer Relevancy: {metrics['answer_relevancy']:.3f}")
    print(f"Context Precision: {metrics['context_precision']:.3f}")
    print(f"Context Recall: {metrics['context_recall']:.3f}")
    print(f"\nReport saved to: {report_path}")

    return report


if __name__ == "__main__":
    run_ragas_evaluation()
