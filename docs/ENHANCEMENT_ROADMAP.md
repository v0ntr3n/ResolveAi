# ResolveAI Enhancement Roadmap

This document outlines a comprehensive 3-week enhancement plan to elevate ResolveAI from a functional MVP to a production-ready, enterprise-grade RAG system.

## Executive Summary

The enhancement plan transforms the current synchronous application into a robust, observable, and scalable system through three focused weeks:

- **Week 1**: System Robustness - Async patterns, structured logging, circuit breakers
- **Week 2**: Quality Assurance - Property-based testing, integration tests, Kubernetes deployment
- **Week 3**: Observability - LangSmith tracing, RAGAS evaluation, Prometheus metrics

---

## Week 1: System Robustness (Days 1-7)

### Overview

Week 1 focuses on improving system reliability, observability, and fault tolerance. These enhancements form the foundation for all subsequent improvements.

### 1.1 Asynchronous Processing Patterns

#### Current State
- Synchronous FastAPI endpoints
- Synchronous database operations (SQLAlchemy)
- Blocking LLM API calls
- Synchronous LangGraph execution

#### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Async Request Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Client Request                                                   │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────┐                                                 │
│  │ FastAPI     │  async def chat()                               │
│  │ Endpoint    │  ├─ await async_db_session()                    │
│  │             │  ├─ await graph.ainvoke()                       │
│  │             │  └─ await background_tasks.log_analytics()      │
│  └─────────────┘                                                 │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────┐                                                 │
│  │ Async       │  • AsyncSession (SQLAlchemy)                    │
│  │ Services    │  • httpx.AsyncClient for LLM                    │
│  │             │  • asyncio.gather() for parallel ops            │
│  └─────────────┘                                                 │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────┐                                                 │
│  │ Background  │  • Analytics logging                            │
│  │ Tasks       │  • Metric aggregation                           │
│  │             │  • Cache invalidation                           │
│  └─────────────┘                                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementation Details

##### 1.1.1 Async Database Layer

**File: `app/data/async_db.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import get_settings

def get_async_engine():
    """Create async database engine."""
    settings = get_settings()
    # Convert sqlite:// to sqlite+aiosqlite://
    db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    return create_async_engine(db_url, echo=False)

def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create async session factory."""
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database session."""
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        yield session
```

##### 1.1.2 Async API Routes

**File: `app/api/routes.py`**

```python
from fastapi import BackgroundTasks

@router.post("/chat")
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_async_db),
    background_tasks: BackgroundTasks
) -> dict:
    """Async chat endpoint with background analytics."""
    conversation_id = payload.conversation_id or str(uuid4())
    
    # Invoke graph asynchronously
    result = await support_graph.ainvoke({
        "message": payload.message,
        "conversation_id": conversation_id,
        "db_session": session
    })
    
    # Log analytics in background
    background_tasks.add_task(
        log_analytics_async,
        conversation_id=conversation_id,
        result=result
    )
    
    return {
        "conversation_id": conversation_id,
        "intent": result["intent"],
        "language": result["language"],
        "response": result["response"],
        "tool_used": result["tool_used"],
        "resolved": result["resolved"],
        "requires_human": result["requires_human"],
        "confidence_score": result["confidence_score"],
    }
```

##### 1.1.3 Async LLM Client

**File: `app/agent/llm.py`**

```python
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_llm_client():
    """Async HTTP client for LLM API with connection pooling."""
    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        yield client

async def classify_intent_with_llm_async(
    message: str,
    api_key: str
) -> tuple[str, float]:
    """Async intent classification using LLM."""
    async with get_llm_client() as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": build_intent_classification_prompt(message)}
                ],
                "temperature": 0,
            }
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Parse structured response
        parsed = json.loads(content)
        return parsed["intent"], parsed["confidence"]
```

#### Migration Strategy

1. **Phase 1: Database Layer** (Day 1-2)
   - Add async session factory
   - Create async versions of service methods
   - Test async database operations

2. **Phase 2: API Layer** (Day 3-4)
   - Convert routes to async
   - Add background task support
   - Update dependency injection

3. **Phase 3: Agent Layer** (Day 5-6)
   - Create async node functions
   - Update LangGraph to use async execution
   - Implement async LLM client

4. **Phase 4: Testing & Validation** (Day 7)
   - Update all tests to use async
   - Performance benchmarking
   - Load testing

#### Expected Benefits

- **Throughput**: 3-5x increase in concurrent request handling
- **Latency**: 20-30% reduction in response time under load
- **Resource Utilization**: 40% reduction in memory usage
- **Scalability**: Better horizontal scaling characteristics

---

### 1.2 Structured Logging Implementation

#### Current State
- Basic Python logging
- No correlation IDs
- No structured format
- Limited context in logs

#### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Structured Logging Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Request → Correlation ID Middleware → Context                   │
│                │                     │                            │
│                │                     ▼                            │
│                │              Structured Logger                   │
│                │              ├─ service: resolveai-api           │
│                │              ├─ version: 1.0.0                   │
│                │              ├─ environment: production          │
│                │              ├─ correlation_id: abc-123          │
│                │              ├─ timestamp: 2026-05-03T...       │
│                │              └─ level: INFO                      │
│                │                                                 │
│                ▼                                                 │
│         Log Aggregation (ELK/Datadog)                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementation Details

##### 1.2.1 Structured Logging Configuration

**File: `app/core/logging.py`**

```python
import logging
import sys
import structlog
from structlog.types import Processor

def configure_logging(service_name: str = "resolveai-api", environment: str = "production"):
    """Configure structured logging for the application."""
    
    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer() if environment == "production" 
            else structlog.dev.ConsoleRenderer(),
        ],
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Set service context
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment=environment,
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
```

##### 1.2.2 Correlation ID Middleware

**File: `app/middleware/correlation.py`**

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Bind to logging context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
```

##### 1.2.3 Request/Response Logging Middleware

**File: `app/middleware/logging.py`**

```python
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
        )
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            return response
            
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise
```

#### Log Format Examples

**Development (Console):**
```
2026-05-03 11:24:00 [info     ] request_started method=POST path=/chat client_ip=127.0.0.1 correlation_id=abc-123
2026-05-03 11:24:01 [info     ] request_completed method=POST path=/chat status_code=200 duration_ms=1245.67 correlation_id=abc-123
```

**Production (JSON):**
```json
{"timestamp": "2026-05-03T11:24:00.123456Z", "level": "info", "event": "request_started", "method": "POST", "path": "/chat", "correlation_id": "abc-123"}
```

#### Benefits

- **Correlation**: Track requests across services with correlation IDs
- **Debugging**: Rich context in every log entry
- **Aggregation**: JSON format ready for ELK, Datadog, CloudWatch
- **Performance**: Async logging with minimal overhead
- **Audit Trail**: Complete request/response logging

---

### 1.3 Circuit Breaker Implementation

#### Current State
- No fault tolerance patterns
- Cascading failures possible
- No fallback mechanisms

#### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Circuit Breaker Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   LLM API    │         │  Database    │                      │
│  │   Circuit    │         │  Circuit     │                      │
│  │   Breaker    │         │  Breaker     │                      │
│  └──────────────┘         └──────────────┘                      │
│        │                         │                               │
│        │ CLOSED                  │ CLOSED                        │
│        │ (normal)                │ (normal)                      │
│        │                         │                               │
│        ├─────────────────────────┤                               │
│        │                         │                               │
│        │ OPEN                    │ OPEN                          │
│        │ (fail fast)             │ (fail fast)                   │
│        │                         │                               │
│        ├─────────────────────────┤                               │
│        │                         │                               │
│        │ HALF_OPEN               │ HALF_OPEN                     │
│        │ (testing)               │ (testing)                     │
│        │                         │                               │
│        ▼                         ▼                               │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   Fallback   │         │   Fallback   │                      │
│  │   Strategy   │         │   Strategy   │                      │
│  │              │         │              │                      │
│  │  Rule-based  │         │  Retry with  │                      │
│  │  Classify    │         │  Backoff     │                      │
│  └──────────────┘         └──────────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementation Details

##### 1.3.1 Circuit Breaker Core

**File: `app/core/circuit_breaker.py`**

```python
import time
from enum import Enum
from typing import Callable, Any
from functools import wraps
import structlog

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: tuple = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open", circuit_name=self.name)
                return True
            return False
        
        return True  # HALF_OPEN
    
    def _record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("circuit_breaker_recovered", circuit_name=self.name)
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _record_failure(self, exc: Exception):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("circuit_breaker_opened", circuit_name=self.name)
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                circuit_name=self.name,
                failure_count=self.failure_count,
            )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exceptions as exc:
            self._record_failure(exc)
            raise

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
```

##### 1.3.2 LLM Circuit Breaker with Fallback

**File: `app/agent/llm.py`**

```python
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

# Circuit breaker for LLM API
llm_circuit = CircuitBreaker(
    name="llm_api",
    failure_threshold=5,
    recovery_timeout=30,
)

async def classify_intent_with_fallback(message: str, api_key: str) -> tuple[str, float]:
    """Classify intent with circuit breaker and fallback."""
    try:
        return await llm_circuit.call(
            classify_intent_with_llm_async,
            message,
            api_key
        )
    except CircuitBreakerOpenError:
        logger.warning("llm_circuit_open_using_fallback")
        # Fallback to rule-based classification
        return _classify_intent_impl(message), 0.7
    except Exception as exc:
        logger.error("llm_classification_failed", error=str(exc))
        return _classify_intent_impl(message), 0.7
```

#### Benefits

- **Fault Tolerance**: Prevent cascading failures
- **Fast Fail**: Quick response when services are down
- **Auto Recovery**: Automatic detection of service recovery
- **Fallback Strategies**: Degraded functionality instead of complete failure

---

## Week 2: Quality Assurance & Deployment (Days 8-14)

### Overview

Week 2 focuses on comprehensive testing strategies and production deployment preparation.

### 2.1 Property-Based Testing

#### Current State
- Unit tests with fixed test cases
- No property-based testing
- Limited edge case coverage

#### Implementation

**File: `tests/property/test_intent_classification.py`**

```python
from hypothesis import given, strategies as st
from app.agent.nodes import classify_intent

# Define strategies
message_strategy = st.text(min_size=1, max_size=500)
order_id_strategy = st.from_regex(r"ORD-\d{6}")

@given(message=message_strategy)
def test_classify_intent_always_returns_valid_intent(message):
    """Property: Classification always returns a valid intent."""
    result = classify_intent(message)
    assert result in {"order_status", "refund", "address_change", "policy_question"}

@given(message=message_strategy)
def test_language_detection_is_deterministic(message):
    """Property: Language detection is deterministic."""
    from app.agent.nodes import detect_language
    result1 = detect_language(message)
    result2 = detect_language(message)
    assert result1 == result2
    assert result1 in {"en", "vi"}

@given(amount=st.floats(min_value=0, max_value=10000))
def test_refund_threshold_logic(amount):
    """Property: Refund threshold logic is consistent."""
    from app.services.refunds import should_auto_approve
    result = should_auto_approve(amount=amount, risk_flag="low")
    # Auto-approve only if amount <= 50 and low risk
    assert result == (amount <= 50.0)
```

**File: `tests/property/test_order_operations.py`**

```python
from hypothesis import given, strategies as st
from app.services.orders import update_shipping_address

address_strategy = st.text(min_size=10, max_size=200)

@given(order_id=order_id_strategy, new_address=address_strategy)
def test_address_update_idempotency(order_id, new_address):
    """Property: Address updates are idempotent."""
    # Update once
    result1 = update_shipping_address(session, order_id, new_address)
    # Update again with same address
    result2 = update_shipping_address(session, order_id, new_address)
    
    assert result1.shipping_address == result2.shipping_address
```

---

### 2.2 Integration Tests

#### Test Architecture

```
tests/
├── integration/
│   ├── test_api_workflow.py      # End-to-end API tests
│   ├── test_db_integration.py    # Database integration
│   ├── test_llm_integration.py   # LLM API integration (mocked)
│   └── test_graph_integration.py # Full graph workflow
└── e2e/
    └── test_user_journeys.py     # Complete user scenarios
```

**File: `tests/integration/test_api_workflow.py`**

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_complete_order_status_workflow():
    """Test complete order status inquiry workflow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit order status query
        response = await client.post(
            "/chat",
            json={"message": "Where is my order ORD-000001?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "order_status"
        assert data["resolved"] is True
        assert "processing" in data["response"].lower()

@pytest.mark.asyncio
async def test_refund_escalation_workflow():
    """Test refund request that requires escalation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # High-value refund request
        response = await client.post(
            "/chat",
            json={"message": "I want a refund for order ORD-000099. It cost $150."}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "refund"
        assert data["requires_human"] is True
        assert data["resolved"] is False
```

**File: `tests/integration/test_graph_integration.py`**

```python
import pytest
from app.agent.graph import build_support_graph
from app.data.db import get_session_factory

@pytest.mark.asyncio
async def test_full_refund_workflow_with_database():
    """Test complete refund workflow with real database."""
    graph = build_support_graph()
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        result = await graph.ainvoke({
            "message": "Refund order ORD-000001",
            "conversation_id": "test-conv-1",
            "db_session": session,
        })
        
        assert result["intent"] == "refund"
        assert result["resolved"] is True
        assert "refund" in result["response"].lower()
```

---

### 2.3 Kubernetes Manifests

#### Deployment Architecture

```
k8s/
├── namespace.yaml              # Dedicated namespace
├── backend-deployment.yaml     # API deployment (3 replicas)
├── backend-service.yaml        # ClusterIP service
├── ui-deployment.yaml          # Streamlit UI deployment
├── ui-service.yaml             # ClusterIP service
├── configmap.yaml              # Configuration
├── secrets.yaml                # Sensitive data
├── ingress.yaml                # External access
├── hpa.yaml                    # Auto-scaling
└── pvc.yaml                    # Persistent storage
```

**File: `k8s/namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: resolveai
  labels:
    app: resolveai
    environment: production
```

**File: `k8s/backend-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resolveai-api
  namespace: resolveai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resolveai-api
  template:
    metadata:
      labels:
        app: resolveai-api
    spec:
      containers:
      - name: api
        image: resolveai-api:latest
        ports:
        - containerPort: 10000
        env:
        - name: DEEPSEEK_API_KEY
          valueFrom:
            secretKeyRef:
              name: resolveai-secrets
              key: deepseek-api-key
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: resolveai-config
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 10000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 10000
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: resolveai-pvc
```

**File: `k8s/backend-service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: resolveai-api
  namespace: resolveai
spec:
  type: ClusterIP
  selector:
    app: resolveai-api
  ports:
  - port: 10000
    targetPort: 10000
```

**File: `k8s/ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: resolveai-ingress
  namespace: resolveai
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.resolveai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: resolveai-api
            port:
              number: 10000
  - host: ui.resolveai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: resolveai-ui
            port:
              number: 8501
```

**File: `k8s/hpa.yaml`**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: resolveai-api-h