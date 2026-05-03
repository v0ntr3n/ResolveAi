# ResolveAI Week 3 Implementation Guide

## Overview

This document provides detailed implementation guidance for Week 3 enhancements: LangSmith Tracing, RAGAS Evaluation, and Prometheus Metrics.

---

## 1. LangSmith Tracing Implementation

### 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              LangSmith Tracing Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request Flow with Tracing:                                      │
│                                                                   │
│  /chat endpoint                                                   │
│       │                                                           │
│       ├─ Span: chat_request                                       │
│       │   ├─ Span: classify_node                                  │
│       │   │   ├─ Span: llm_classification                         │
│       │   │   │   └─ LLM Call to DeepSeek                         │
│       │   │   └─ Span: entity_extraction                          │
│       │   │                                                       │
│       │   ├─ Span: execute_refund_node                            │
│       │   │   ├─ Span: db_query                                   │
│       │   │   └─ Span: refund_logic                               │
│       │   │                                                       │
│       │   └─ Span: log_node                                       │
│       │       └─ Span: db_insert                                  │
│       │                                                           │
│       └─ LangSmith Dashboard                                      │
│           ├─ Trace Timeline                                       │
│           ├─ Latency Breakdown                                    │
│           ├─ LLM Token Usage                                      │
│           └─ Error Tracking                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Configuration

**File: `app/core/config.py`**

Add LangSmith configuration to Settings:

```python
class Settings(BaseSettings):
    # Existing settings...
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DATABASE_URL: str = "sqlite:///./data/orders.db"
    VECTOR_INDEX_DIR: str = "./data/vector_index"
    AUTO_SEED_DATA: bool = True
    REFUND_APPROVAL_THRESHOLD: float = 50.0
    
    # LangSmith tracing
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "resolveai-production"
    LANGSMITH_ORG: str = ""
```

**File: `app/core/tracing.py`**

Create LangSmith configuration module:

```python
import os
from langsmith import Client
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()

def configure_tracing():
    """Configure LangSmith tracing for the application."""
    settings = get_settings()
    
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or "resolveai-production"
        
        # Initialize LangSmith client
        client = Client()
        logger.info(
            "langsmith_tracing_configured",
            project=settings.LANGSMITH_PROJECT,
        )
        return client
    
    logger.info("langsmith_tracing_disabled")
    return None

def get_trace_url(run_id: str) -> str:
    """Get LangSmith trace URL for a specific run."""
    settings = get_settings()
    if settings.LANGSMITH_API_KEY:
        return f"https://smith.langchain.com/o/{settings.LANGSMITH_ORG}/projects/p/{settings.LANGSMITH_PROJECT}/r/{run_id}"
    return ""
```

### 1.3 Traced LLM Calls

**File: `app/agent/llm.py`**

Update LLM functions with tracing:

```python
from langsmith.run_helpers import traceable
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import json

@traceable(name="llm_classification", run_type="llm")
async def classify_intent_with_tracing(
    message: str,
    api_key: str
) -> tuple[str, float]:
    """Classify intent with LangSmith tracing."""
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    
    prompt = build_intent_classification_prompt(message)
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    # Parse response
    parsed = json.loads(response.content)
    
    return parsed["intent"], parsed["confidence"]

@traceable(name="llm_policy_generation", run_type="llm")
async def generate_policy_answer_with_tracing(
    question: str,
    policy_context: str,
    language: str,
    api_key: str
) -> str:
    """Generate policy answer with LangSmith tracing."""
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    
    prompt = build_policy_prompt(question, policy_context, language)
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    return response.content
```

### 1.4 Traced Agent Nodes

**File: `app/agent/nodes.py`**

Add tracing decorators to nodes:

```python
from langsmith.run_helpers import traceable

@traceable(name="classify_node", run_type="chain")
async def classify_node_async(state: SupportState) -> dict:
    """Classify node with tracing."""
    message = state["message"]
    
    # Language detection
    language = detect_language(message)
    
    # Intent classification with tracing
    if get_settings().DEEPSEEK_API_KEY:
        intent, confidence = await classify_intent_with_tracing(
            message,
            get_settings().DEEPSEEK_API_KEY
        )
    else:
        intent = classify_intent_cached(message)
        confidence = 0.8
    
    # Entity extraction
    order_id = extract_order_id(message)
    new_address = extract_address(message)
    
    return {
        "language": language,
        "intent": intent,
        "confidence_score": confidence,
        "order_id": order_id,
        "new_address": new_address,
        "tool_used": f"classify_{intent}",
    }

@traceable(name="refund_node", run_type="chain")
async def execute_refund_node_async(state: SupportState) -> dict:
    """Refund node with tracing."""
    session = state["db_session"]
    order_id = state["order_id"]
    
    # Get order
    order = await get_order_by_id_async(session, order_id)
    
    # Process refund
    decision = await process_refund_request_async(
        session,
        order_id=order_id,
        reason="customer_request"
    )
    
    return {
        "response": build_refund_response(decision, state["language"]),
        "resolved": decision.decision == "approved",
        "requires_human": decision.decision == "requires_human",
        "action_result": decision.model_dump(),
    }
```

### 1.5 API Integration

**File: `app/api/routes.py`**

Add trace URL to API responses:

```python
from langsmith.run_helpers import traceable
from langsmith import get_current_run_tree

@router.post("/chat")
@traceable(name="chat_endpoint", run_type="chain")
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_async_db),
    background_tasks: BackgroundTasks
) -> dict:
    """Chat endpoint with full tracing."""
    conversation_id = payload.conversation_id or str(uuid4())
    
    # Invoke graph with tracing
    result = await support_graph.ainvoke({
        "message": payload.message,
        "conversation_id": conversation_id,
        "db_session": session
    })
    
    # Get trace URL
    run = get_current_run_tree()
    trace_url = get_trace_url(run.id) if run else None
    
    response = {
        "conversation_id": conversation_id,
        "intent": result["intent"],
        "language": result["language"],
        "response": result["response"],
        "tool_used": result["tool_used"],
        "resolved": result["resolved"],
        "requires_human": result["requires_human"],
        "confidence_score": result["confidence_score"],
    }
    
    if trace_url:
        response["trace_url"] = trace_url
    
    return response
```

---

## 2. RAGAS Evaluation Implementation

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              RAGAS Evaluation Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Evaluation Workflow:                                            │
│                                                                   │
│  ┌──────────────┐                                                │
│  │  Test Cases  │ (20+ bilingual queries)                       │
│  │  (queries +  │                                                │
│  │  expected)   │                                                │
│  └──────┬───────┘                                                │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │  RAG Pipeline│                                                │
│  │  Execution   │ → Generate responses                           │
│  └──────┬───────┘                                                │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────────────────────────────────┐               │
│  │  RAGAS Metrics                               │               │
│  │  ├─ Faithfulness (0-1)                       │               │
│  │  │   └─ Answer grounded in context           │               │
│  │  ├─ Answer Relevancy (0-1)                   │               │
│  │  │   └─ Answer addresses the question        │               │
│  │  ├─ Context Precision (0-1)                  │               │
│  │  │   └─ Retrieved context is relevant        │               │
│  │  └─ Context Recall (0-1)                     │               │
│  │      └─ All relevant context retrieved       │               │
│  └──────────────────────────────────────────────┘               │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │  Evaluation  │                                                │
│  │  Report      │ → JSON + Dashboard                             │
│  └──────────────┘                                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Dependencies

Add to `requirements.txt`:

```
ragas>=0.1.0
datasets>=2.14.0
```

### 2.3 RAGAS Evaluator

**File: `app/evals/ragas_eval.py`**

```python
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
import structlog

logger = structlog.get_logger()

class RAGASEvaluator:
    """RAGAS-based RAG evaluation."""
    
    def __init__(self):
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
        
        # Define metrics
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]
    
    def prepare_dataset(
        self,
        test_cases: list[dict]
    ) -> Dataset:
        """Prepare test cases for RAGAS evaluation."""
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
    
    async def evaluate_rag(
        self,
        test_cases: list[dict]
    ) -> dict:
        """Evaluate RAG pipeline using RAGAS metrics."""
        dataset = self.prepare_dataset(test_cases)
        
        logger.info(
            "ragas_evaluation_started",
            num_cases=len(test_cases),
        )
        
        results = evaluate(
            dataset,
            metrics=self.metrics,
            llm=self.llm,
            embeddings=self.embeddings,
        )
        
        logger.info(
            "ragas_evaluation_completed",
            results=results,
        )
        
        return {
            "faithfulness": float(results["faithfulness"]),
            "answer_relevancy": float(results["answer_relevancy"]),
            "context_precision": float(results["context_precision"]),
            "context_recall": float(results["context_recall"]),
            "overall_score": sum(results.values()) / len(results),
        }
```

### 2.4 Evaluation Pipeline

**File: `app/evals/evaluation_pipeline.py`**

```python
import asyncio
import json
from pathlib import Path
from datetime import datetime, UTC
from app.evals.ragas_eval import RAGASEvaluator
from app.agent.graph import build_support_graph
from app.services.retrieval import retrieve_policy_context
from app.data.db import get_session_factory
import structlog

logger = structlog.get_logger()

async def run_ragas_evaluation(limit: int | None = None):
    """Run complete RAGAS evaluation pipeline."""
    # Load test cases
    test_cases_path = Path("data/evals/ragas_test_cases.json")
    
    if not test_cases_path.exists():
        logger.error("ragas_test_cases_not_found", path=str(test_cases_path))
        return None
    
    with open(test_cases_path) as f:
        test_cases = json.load(f)
    
    if limit:
        test_cases = test_cases[:limit]
    
    # Build graph
    graph = build_support_graph()
    session_factory = get_session_factory()
    
    # Generate responses
    evaluation_cases = []
    
    for case in test_cases:
        logger.info(
            "processing_test_case",
            case_id=case["id"],
            query=case["query"][:50],
        )
        
        # Execute RAG pipeline
        async with session_factory() as session:
            result = await graph.ainvoke({
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
    evaluator = RAGASEvaluator()
    metrics = await evaluator.evaluate_rag(evaluation_cases)
    
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
    
    logger.info(
        "ragas_evaluation_report_saved",
        path=str(report_path),
        overall_score=metrics["overall_score"],
    )
    
    return report

if __name__ == "__main__":
    asyncio.run(run_ragas_evaluation())
```

### 2.5 Test Cases

**File: `data/evals/ragas_test_cases.json`**

```json
[
  {
    "id": "eval-001",
    "query": "What is your refund policy?",
    "expected_answer": "Refunds are available within 7 days of purchase for unused items in original packaging. Refunds after 7 days require manager approval.",
    "category": "policy_question"
  },
  {
    "id": "eval-002",
    "query": "How long does shipping take?",
    "expected_answer": "Standard shipping takes 5-7 business days. Express shipping takes 2-3 business days. International shipping may take 10-14 business days.",
    "category": "policy_question"
  },
  {
    "id": "eval-003",
    "query": "Chính sách hoàn tiền là gì?",
    "expected_answer": "Hoàn tiền trong vòng 7 ngày sau khi mua cho các mặt hàng chưa sử dụng trong bao bì gốc. Hoàn tiền sau 7 ngày cần sự chấp thuận của quản lý.",
    "category": "policy_question"
  }
]
```

---

## 3. Prometheus Metrics Implementation

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Prometheus Metrics Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │  FastAPI     │         │  Prometheus  │                      │
│  │  App         │────────▶│  Server      │                      │
│  │              │         │              │                      │
│  │  /metrics    │         │  Scrape      │                      │
│  └──────────────┘         │  every 15s   │                      │
│                           └──────┬───────┘                      │
│                                  │                               │
│                                  ▼                               │
│                           ┌──────────────┐                      │
│                           │   Grafana    │                      │
│                           │   Dashboard  │                      │
│                           └──────────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Dependencies

Add to `requirements.txt`:

```
prometheus-client>=0.19.0
```

### 3.3 Metrics Registry

**File: `app/core/metrics.py`**

```python
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import structlog

logger = structlog.get_logger()

# Create custom registry
registry = CollectorRegistry()

# Request Metrics
REQUEST_COUNT = Counter(
    'resolveai_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'resolveai_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

# Business Metrics
INTENT_CLASSIFICATION = Counter(
    'resolveai_intent_classification_total',
    'Total intent classifications',
    ['intent', 'language'],
    registry=registry
)

RESOLUTION_RATE = Gauge(
    'resolveai_resolution_rate',
    'Current resolution rate',
    registry=registry
)

ESCALATION_COUNT = Counter(
    'resolveai_escalations_total',
    'Total number of escalations',
    ['intent', 'reason'],
    registry=registry
)

# LLM Metrics
LLM_CALL_DURATION = Histogram(
    'resolveai_llm_call_duration_seconds',
    'LLM API call duration',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# Cache Metrics
CACHE_HITS = Counter(
    'resolveai_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

CACHE_MISSES = Counter(
    'resolveai_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

# Circuit Breaker Metrics
CIRCUIT_BREAKER_STATE = Gauge(
    'resolveai_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['circuit_name'],
    registry=registry
)

# Application Info
APP_INFO = Info(
    'resolveai_app',
    'Application information',
    registry=registry
)

APP_INFO.info({
    'version': '1.0.0',
    'service': 'resolveai-api',
})

def metrics_endpoint() -> Response:
    """FastAPI endpoint for Prometheus metrics."""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )
```

### 3.4 Instrumented Middleware

**File: `app/middleware/metrics.py`**

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record start time
        start_time = time.perf_counter()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.perf_counter() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
        
        return response
```

### 3.5 API Endpoint

**File: `app/api/routes.py`**

Add metrics endpoint:

```python
from app.core.metrics import metrics_endpoint

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()
```

---

## 4. Configuration Summary

### 4.1 Environment Variables

Add to `.env`:

```bash
# LangSmith Tracing
LANGSMITH_API_KEY=lsv2_pt_xxxxx
LANGSMITH_PROJECT=resolveai-production
LANGSMITH_ORG=your-org-id

# RAGAS Evaluation (uses OpenAI for metrics)
OPENAI_API_KEY=sk-xxxxx

# Existing
DEEPSEEK_API_KEY=sk-xxxxx
DATABASE_URL=sqlite:///./data/orders.db
```

### 4.2 Dependencies Update

**File: `requirements.txt`**

Add:

```
# Week 3: Observability
langsmith>=0.1.0
ragas>=0.1.0
datasets>=2.14.0
prometheus-client>=0.19.0
```

---

## 5. Testing & Validation

### 5.1 LangSmith Tracing Test

```bash
# Run with tracing enabled
export LANGSMITH_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true

# Make API call
curl -X POST http://localhost:10000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the refund policy?"}'

# Check trace URL in response
# Visit LangSmith dashboard to view detailed trace
```

### 5.2 RAGAS Evaluation Test

```bash
# Run evaluation
python -m app.evals.evaluation_pipeline

# Check report
cat data/evals/ragas_report.json
```

### 5.3 Prometheus Metrics Test

```bash
# Access metrics endpoint
curl http://localhost:10000/metrics

# Expected output:
# HELP resolveai_requests_total Total number of requests
# TYPE resolveai_requests_total counter
# resolveai_requests_total{endpoint="/chat",method="POST",status_code="200"} 5.0
```

---

## 6. Monitoring Dashboard

### 6.1 Grafana Setup

**File: `docker-compose.monitoring.yml`**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
```

### 6.2 Prometheus Configuration

**File: `monitoring/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'resolveai-api'
    static_configs:
      - targets: ['host.docker.internal:10000']
    metrics_path: '/metrics'
```

---

## 7. Success Criteria

Week 3 implementation is complete when:

- [ ] LangSmith tracing captures all node executions
- [ ] Trace URLs are included in API responses
- [ ] RAGAS evaluation runs successfully on test cases
- [ ] RAGAS report shows all 4 metrics
- [ ] Prometheus /metrics endpoint returns valid metrics
- [ ] Request latency and count metrics are recorded
- [ ] Intent classification distribution is tracked
- [ ] Grafana dashboard displays metrics correctly

---

## 8. Next Steps

After Week 3:

1. Set up alerting rules in Prometheus
2. Create custom Grafana dashboards for business KPIs
3. Implement automated RAGAS evaluation in CI/CD
4. Add LangSmith feedback collection for continuous improvement
5. Document operational runbooks for monitoring
