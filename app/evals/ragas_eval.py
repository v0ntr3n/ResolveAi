"""RAGAS-based RAG evaluation for quality metrics."""

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

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


def _get_embeddings_model(settings) -> OpenAIEmbeddings:
    """Get embeddings model - supports llama.cpp server or OpenAI-compatible APIs.
    
    Priority:
    1. EMBEDDING_API_BASE (llama.cpp server or custom API)
    2. OPENAI_API_KEY
    3. DEEPSEEK_API_KEY (DeepSeek doesn't have embeddings, fallback to error)
    """
    # Priority 1: Custom embedding API (llama.cpp server)
    if settings.EMBEDDING_API_BASE:
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY or "dummy-key",
            base_url=settings.EMBEDDING_API_BASE,
        )
    
    # Priority 2: OpenAI embeddings
    if settings.OPENAI_API_KEY:
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY,
        )
    
    # No embeddings available
    raise ValueError(
        "Embeddings required for RAGAS evaluation. "
        "Set EMBEDDING_API_BASE (for llama.cpp server) or OPENAI_API_KEY"
    )


class RAGASEvaluator:
    """RAGAS-based RAG evaluation for measuring response quality."""

    def __init__(self):
        """Initialize RAGAS evaluator with LLM and embeddings.
        
        Supports:
        - DeepSeek API for LLM
        - llama.cpp server for embeddings
        - OpenAI API for both
        """
        settings = get_settings()

        # Initialize LLM - prefer DeepSeek if available
        if settings.DEEPSEEK_API_KEY:
            # DeepSeek uses OpenAI-compatible API
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",
            )
        elif settings.OPENAI_API_KEY:
            # Use OpenAI for LLM
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
            )
        else:
            raise ValueError("Either DEEPSEEK_API_KEY or OPENAI_API_KEY required for LLM")
        
        # Initialize embeddings - supports llama.cpp server
        self.embeddings = _get_embeddings_model(settings)

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

        # Handle RAGAS results - they may be lists or single values
        def get_metric_value(results, key: str) -> float:
            val = results[key]
            if isinstance(val, list):
                # Return average of list values
                return sum(v for v in val if v is not None) / len([v for v in val if v is not None]) if val else 0.0
            return float(val) if val is not None else 0.0

        faithfulness = get_metric_value(results, "faithfulness")
        answer_relevancy = get_metric_value(results, "answer_relevancy")
        context_precision = get_metric_value(results, "context_precision")
        context_recall = get_metric_value(results, "context_recall")

        return {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_precision": context_precision,
            "context_recall": context_recall,
            "overall_score": (faithfulness + answer_relevancy + context_precision + context_recall) / 4,
        }
