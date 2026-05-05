# ResolveAI Architecture

This document provides a comprehensive overview of the ResolveAI system architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ResolveAI System                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Next.js UI    │  ← Bilingual Chat Interface (English/Vietnamese)
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│  Rate Limiter    │────▶│  Exception      │
│   Backend       │     │  Middleware      │     │  Handlers       │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LangGraph Agent Workflow                             │
│  ┌─────────┐    ┌──────────────┐    ┌───────────────────────────────────┐   │
│  │ START   │───▶│  classify    │───▶│  Conditional Router (by intent)   │   │
│  └─────────┘    └──────────────┘    └───────────┬───────────────────────┘   │
│                                                 │                            │
│         ┌───────────────────────────────────────┼───────────────────────┐    │
│         │                   │                   │                   │    │    │
│         ▼                   ▼                   ▼                   ▼    │    │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐│
│  │order_status│      │  refund    │      │  address   │      │  policy    ││
│  │    node    │      │   node     │      │  _change   │      │   node     ││
│  └─────┬──────┘      └─────┬──────┘      └─────┬──────┘      └─────┬──────┘│
│        │                   │                   │                   │        │
│        │                   │                   │                   ▼        │
│        │                   │                   │           ┌────────────┐  │
│        │                   │                   │           │ retrieve_  │  │
│        │                   │                   │           │  policy    │  │
│        │                   │                   │           └─────┬──────┘  │
│        │                   │                   │                 │         │
│        └───────────────────┴───────────────────┴─────────────────┘         │
│                                    │                                        │
│                                    ▼                                        │
│                             ┌────────────┐                                  │
│                             │    log     │                                  │
│                             │   node     │                                  │
│                             └─────┬──────┘                                  │
│                                   │                                         │
│                                   ▼                                         │
│                              ┌─────────┐                                    │
│                              │   END   │                                    │
│                              └─────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├──────────────────────┬──────────────────────┬─────────────────┐
         ▼                      ▼                      ▼                 ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ ┌────────────┐
│  Multi-Layer    │    │   FAISS Vector  │    │    SQLite       │ │  DeepSeek  │
│  LRU Cache      │    │   Search Index  │    │   Database      │ │    LLM     │
│  (Orders,       │    │   (Semantic     │    │   (Orders,      │ │  (Intent,  │
│   Policies)     │    │    Retrieval)   │    │    Escalations) │ │   Policy)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘ └────────────┘
```

## Component Details

### 1. Frontend Layer (Next.js)

**Directory:** `ui-nextjs/`

```
Responsibilities:
- Bilingual chat interface
- Real-time metrics dashboard
- Escalation visualization
- Conversation history

Key Features:
- Language detection (English/Vietnamese)
- Decision transparency (intent, confidence, tool used)
- Session state management
- Modern React with Framer Motion animations
- Responsive design with Tailwind CSS
```

### 2. API Layer (FastAPI)

**File:** `app/main.py`, `app/api/routes.py`

```
Endpoints:
├── POST /chat          - Main conversation endpoint
├── GET  /metrics       - Dashboard metrics
├── GET  /performance   - Node performance statistics
├── GET  /escalations   - Recent escalations list
└── GET  /health        - Health check

Middleware:
- Rate limiting (60 req/min, burst: 10)
- Exception handling
- Request logging
```

### 3. Agent Layer (LangGraph)

**Files:** `app/agent/graph.py`, `app/agent/nodes.py`, `app/agent/state.py`

#### State Schema

```python
class SupportState(TypedDict, total=False):
    message: str                    # User input
    conversation_id: str            # Session identifier
    db_session: Session             # Database session
    language: str                   # Detected language (en/vi)
    intent: str                     # Classified intent
    order_id: str | None            # Extracted order ID
    new_address: str | None         # Extracted new address
    policy_context: dict | None     # Retrieved policy
    tool_used: str                  # Tool identifier
    response: str                   # Final response
    resolved: bool                  # Resolution status
    requires_human: bool            # Escalation flag
    confidence_score: float         # Classification confidence
    action_result: Any              # Action execution result
```

#### Node Functions

| Node | Purpose | Tools Used |
|------|---------|------------|
| `classify` | Intent classification + entity extraction | LLM + Rules |
| `retrieve_policy` | Semantic search for policies | FAISS |
| `order_status` | Order lookup and status | Database |
| `refund` | Refund processing with guardrails | Database + Rules |
| `address_change` | Address update with validation | Database |
| `policy` | Policy Q&A response | LLM + Context |
| `log` | Conversation logging + analytics | Database |

### 4. Services Layer

#### 4.1 Retrieval Service (`app/services/retrieval.py`)

```
RAG Pipeline:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User       │────▶│  Document   │────▶│   FAISS     │
│  Query      │     │  Chunking   │     │   Index     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐     ┌──────▼──────┐
                    │   Policy    │◀────│   Vector    │
                    │   Context   │     │   Search    │
                    └─────────────┘     └─────────────┘

Configuration:
- Chunk size: 500 characters
- Embedding model: text-embedding-ada-002
- Index type: FAISS IndexFlatL2
- Persistence: Local filesystem
```

#### 4.2 Caching Service (`app/services/cache.py`)

```
Multi-Layer Cache Architecture:
┌─────────────────────────────────────────────────┐
│                  LRU Cache                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Order Cache │  │Policy Cache │  │ Metrics  │ │
│  │ (500 items) │  │ (200 items) │  │ (100)    │ │
│  │ TTL: 180s   │  │ TTL: 300s   │  │ TTL: 60s │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
│                                                  │
│  Features:                                       │
│  - Thread-safe operations                        │
│  - TTL-based expiration                          │
│  - Hash-based key generation                     │
│  - Statistics tracking                           │
└─────────────────────────────────────────────────┘
```

#### 4.3 Order Service (`app/services/orders.py`)

```
Operations:
- get_order_by_id()       - Order retrieval
- update_shipping_address() - Address modification
- Business rules validation
```

#### 4.4 Refund Service (`app/services/refunds.py`)

```
Refund Decision Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Validate   │────▶│  Check      │────▶│  Apply      │
│  Order      │     │  Guardrails │     │  Decision   │
└─────────────┘     └─────────────┘     └─────────────┘

Guardrails:
- Amount > $50 → Human approval required
- Risk flag: medium/high → Human review
- Evidence required for damaged/wrong_item claims
```

### 5. Data Layer

#### 5.1 Database Models (`app/data/models.py`)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Order       │     │   Escalation    │     │ ConversationLog │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ order_id (PK)   │     │ id (PK)         │     │ id (PK)         │
│ customer_email  │     │ order_id (FK)   │     │ conversation_id │
│ customer_name   │     │ intent          │     │ user_message    │
│ status          │     │ reason          │     │ detected_lang   │
│ tracking_number │     │ status          │     │ intent          │
│ amount          │     │ evidence_needed │     │ resolved        │
│ refund_status   │     │ sla_hours       │     │ tool_used       │
│ risk_flag       │     │ review_notes    │     │ confidence      │
│ ...             │     │ ...             │     │ latency_ms      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 6. LLM Integration

**File:** `app/agent/llm.py`

```
LLM Operations:
┌─────────────────────────────────────────────────┐
│              DeepSeek API Integration            │
├─────────────────────────────────────────────────┤
│  Model: deepseek-chat                           │
│  Temperature: 0 (deterministic)                  │
│  Base URL: https://api.deepseek.com             │
│                                                  │
│  Functions:                                      │
│  ├── classify_intent_with_llm()                 │
│  │   └── Intent classification with fallback    │
│  └── generate_policy_answer()                   │
│      └── Policy Q&A with context                │
│                                                  │
│  Fallback Strategy:                              │
│  LLM Error → Rule-based Classification          │
└─────────────────────────────────────────────────┘
```

## Data Flow

### Example: Refund Request Flow

```
1. User Input: "Refund order ORD-000245"
   │
2. API Layer: POST /chat
   │
3. Agent Workflow:
   │
   ├─▶ classify_node()
   │   ├── Detect language: "en"
   │   ├── Classify intent: "refund"
   │   ├── Extract order_id: "ORD-000245"
   │   └── Confidence: 0.92
   │
   ├─▶ route_intent() → "refund"
   │
   ├─▶ execute_refund_node()
   │   ├── Get order from database
   │   ├── Check refund eligibility
   │   ├── Evaluate amount vs threshold ($50)
   │   ├── Check risk flags
   │   └── Decision:
   │       ├── Amount < $50 + low risk → APPROVED
   │       └── Amount > $50 OR high risk → REQUIRES_HUMAN
   │
   └─▶ log_node()
       ├── Log conversation
       ├── Update metrics
       └── Create escalation if needed

4. Response to User:
   {
     "response": "Your refund has been processed...",
     "resolved": true,
     "requires_human": false,
     "confidence_score": 0.92
   }
```

## Performance Optimizations

### Caching Strategy

| Cache Layer | Target | TTL | Hit Rate Impact |
|-------------|--------|-----|-----------------|
| Order Cache | Order lookups | 180s | 80% reduction in DB queries |
| Policy Cache | Policy retrieval | 300s | 73% latency reduction |
| Metrics Cache | Dashboard stats | 60s | Real-time feel |

### Performance Metrics

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Order Status | 120ms | 25ms | 80% faster |
| Refund | 150ms | 40ms | 73% faster |
| Policy Q&A | 300ms | 80ms | 73% faster |
| Address Change | 100ms | 20ms | 80% faster |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Render Platform                         │
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │   resolveai-api      │      │   resolveai-ui       │     │
│  │   (FastAPI)          │      │   (Next.js)          │     │
│  │   Port: 8000         │◀────▶│   Port: 3000         │     │
│  │   Region: Singapore  │      │   Region: Singapore  │     │
│  └──────────┬───────────┘      └──────────────────────┘     │
│             │                                                │
│             │ Private Networking                             │
│             │                                                │
│  ┌──────────▼───────────┐                                   │
│  │   SQLite Database    │                                   │
│  │   (orders.db)        │                                   │
│  └──────────────────────┘                                   │
│                                                              │
│  Environment Variables:                                      │
│  - DEEPSEEK_API_KEY (secret)                                │
│  - DATABASE_URL                                             │
│  - AUTO_SEED_DATA=true                                      │
│  - REFUND_APPROVAL_THRESHOLD=50.0                           │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Available Metrics

```
GET /metrics
{
  "total_conversations": 150,
  "resolved_count": 120,
  "escalation_count": 15,
  "resolution_rate": 0.80,
  "average_confidence": 0.89
}

GET /performance
{
  "classify": {
    "count": 150,
    "avg": 0.05,
    "min": 0.01,
    "max": 0.15
  },
  "refund": {
    "count": 45,
    "avg": 0.04,
    "min": 0.02,
    "max": 0.12
  }
}
```

## Security Considerations

1. **Rate Limiting**: 60 requests/minute with burst protection
2. **Input Validation**: Pydantic models for all inputs
3. **Non-root Container**: Docker runs as unprivileged user
4. **API Key Protection**: Secrets managed via environment variables
5. **SQL Injection Prevention**: SQLAlchemy parameterized queries

## Scaling Considerations

### Horizontal Scaling

```
Current: Single instance (SQLite)
Target: Multiple replicas (PostgreSQL)

Changes Required:
1. Replace SQLite with PostgreSQL
2. Add connection pooling
3. Implement Redis for distributed caching
4. Add load balancer
```

### Async Migration Path

```
Phase 1: Convert blocking I/O to async
Phase 2: Use AsyncSession for database
Phase 3: Implement async LLM calls
Phase 4: Add streaming responses
```

---

*Architecture documentation generated for ResolveAI portfolio presentation.*
