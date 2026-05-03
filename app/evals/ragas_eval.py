"""RAGAS-based RAG evaluation for quality metrics."""

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import get_settings


class RAGASEvaluator:
    """RAGAS-based RAG evaluation for measuring response quality."""

    def __init__(self):
        """Initialize RAGAS evaluator with LLM and embeddings."""
        settings = get_settings()

        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required for RAGAS evaluation")

        # Initialize LLM and embeddings for RAGAS
        self.llm = ChatOpenAI(
            model="gpt-4",
            api_key=settings.OPENAI_API_KEY,
        )

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY,
        )

        # Define metrics to evaluate
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]

    def prepare_dataset(self, test_cases: list[dict]) -> Dataset:
        """Prepare test cases for RAGAS evaluation.

        Args:
            test_cases: List of test cases with query, generated_answer,
                       retrieved_contexts, and expected_answer.

        Returns:
            Dataset formatted for RAGAS evaluation.
        """
        data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
        }

        for case in test_cases:
            data["question"].append(case["query"])
            data["answer"].append(case["generated_answer"])
            data["contexts"].append(case["retrieved_contexts"])
            data["ground_truth"].append(case["expected_answer"])

        return Dataset.from_dict(data)

    def evaluate_rag(self, test_cases: list[dict]) -> dict:
        """Evaluate RAG pipeline using RAGAS metrics.

        Args:
            test_cases: List of test cases to evaluate.

        Returns:
            Dictionary with metric scores.
        """
        dataset = self.prepare_dataset(test_cases)

        results = evaluate(
            dataset,
            metrics=self.metrics,
            llm=self.llm,
            embeddings=self.embeddings,
        )

        return {
            "faithfulness": float(results["faithfulness"]),
            "answer_relevancy": float(results["answer_relevancy"]),
            "context_precision": float(results["context_precision"]),
            "context_recall": float(results["context_recall"]),
            "overall_score": sum(results.values()) / len(results),
        }
