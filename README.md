# ResolveAI

ResolveAI is a bilingual autonomous Tier-1 support system built with LangGraph, FastAPI, and Streamlit. It provides intelligent customer support for order status inquiries, refund requests, address changes, and policy questions in both English and Vietnamese.

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Project Overview

### Purpose

ResolveAI demonstrates a production-ready RAG (Retrieval-Augmented Generation) system for customer support automation. It showcases:

- **Intelligent Intent Classification**: LLM-powered with rule-based fallback
- **Semantic Search**: FAISS-based vector search for policy documents
- **Multi-Layer Caching**: LRU caches for orders, policies, and metrics
- **Robust Error Handling**: Custom exceptions, validation utilities, and circuit breakers
- **API Rate Limiting**: Protection against abuse with configurable limits
- **Performance Monitoring**: Real-time tracking with Prometheus metrics
- **Distributed Tracing**: LangSmith integration for workflow visibility
- **RAG Quality Evaluation**: RAGAS metrics for response quality assessment

### Supported Operations

| Operation | Description | Guardrails |
|-----------|-------------|------------|
| Order Status | Track order location and delivery status | None |
| Refund Processing | Handle refund requests | Amount > $50 requires human approval |
| Address Change | Update shipping address | Only before shipment, not for risky orders |
| Policy Q&A | Answer policy questions | Semantic search with context |
| Evidence Handling | Request evidence for damaged items | Photo required for damaged/wrong-item claims |

### Language Support

- **English**: Full support for all operations
- **Vietnamese**: Full support for all operations

---

## Prerequisites

### System Requirements

- **Python**: 3.12 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Disk Space**: 1GB for application + data

### Required Software

- **uv**: Fast Python package installer (recommended)
  ```bash
  # Install uv
  pip install uv
  ```

- **Git**: For cloning the repository
  ```bash
  # Verify git installation
  git --version
  ```

### Optional (for Docker deployment)

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/resolveai.git
cd resolveai
```

### Step 2: Create Virtual Environment and Install Dependencies

Using uv (recommended):
```bash
# Create virtual environment and install dependencies
uv sync

# Or install with dev dependencies
uv sync --all-groups
```

Using pip (alternative):
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# See Environment Configuration section for details
```

### Step 4: Initialize Data

```bash
# Seed the database with sample orders
uv run python -m app.data.seed
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Core Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DATABASE_URL=sqlite:///./data/orders.db
VECTOR_INDEX_DIR=./data/vector_index
AUTO_SEED_DATA=true
REFUND_APPROVAL_THRESHOLD=50.0
```

### Optional Environment Variables

#### LangSmith Tracing (for workflow visibility)

```bash
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=resolveai-production
LANGSMITH_ORG=your_org_id
```

#### RAGAS Evaluation (for RAG quality metrics)

```bash
OPENAI_API_KEY=your_openai_key_here
```

#### Prometheus Metrics

```bash
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Obtaining API Keys

| Service | Purpose | How to Obtain |
|---------|---------|---------------|
| DeepSeek | LLM for intent classification and responses | [DeepSeek Platform](https://platform.deepseek.com/) |
| LangSmith | Distributed tracing for LLM workflows | [LangSmith](https://smith.langchain.com/) |
| OpenAI | RAGAS evaluation metrics | [OpenAI Platform](https://platform.openai.com/) |

---

## Database Setup

### SQLite (Default)

The default configuration uses SQLite, which requires no additional setup:

```bash
# Database is automatically created at data/orders.db
# Seed initial data:
uv run python -m app.data.seed
```

### PostgreSQL (Production)

For production, use PostgreSQL:

1. Install PostgreSQL and create a database:
   ```bash
   createdb resolveai
   ```

2. Update `DATABASE_URL` in `.env`:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/resolveai
   ```

3. Run migrations:
   ```bash
   uv run python -m app.data.seed
   ```

### Database Schema

The database contains three main tables:

- **orders**: Customer orders with status, tracking, and refund information
- **escalations**: Human intervention requests
- **conversation_logs**: Conversation history and analytics

---

## Running the Application

### Development Mode

#### Start Backend API

```bash
# Using uvicorn with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```

#### Start Streamlit UI

```bash
# In a separate terminal
uv run streamlit run ui/app.py
```

#### Access the Application

- **API**: http://localhost:10000
- **API Documentation**: http://localhost:10000/docs
- **Streamlit UI**: http://localhost:8501

### Production Mode

#### Using Gunicorn

```bash
# Install gunicorn
uv pip install gunicorn

# Run with multiple workers
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:10000
```

#### Using Docker

See [Docker Deployment](#docker-deployment) section.

### Demo Scripts

Windows PowerShell:
```powershell
# Run smoke test
powershell -ExecutionPolicy Bypass -File scripts/demo_smoke.ps1

# Seed demo orders for testing
powershell -ExecutionPolicy Bypass -File scripts/seed_demo.ps1
```

### Demo Orders

The project includes predefined demo orders for testing various scenarios:

```bash
# Seed demo orders (15 orders with various test scenarios)
uv run python -m app.data.seed_demo
```

**Demo Order Scenarios:**

| Order ID | Scenario | Language | Status |
|----------|----------|----------|--------|
| DEMO-001 | Standard delivered, refund eligible | English | Delivered |
| DEMO-002 | Damaged fragile item, needs photo evidence | Vietnamese | Delivered |
| DEMO-003 | Pending order, address change allowed | English | Pending |
| DEMO-004 | Processing, special handling, medium risk | Vietnamese | Processing |
| DEMO-005 | Shipped, cannot change address | English | Shipped |
| DEMO-006 | Refund already approved (wrong item) | Vietnamese | Delivered |
| DEMO-007 | Out for delivery, fragile | English | Out for Delivery |
| DEMO-008 | High value (>$120), NOT auto-refund eligible | Vietnamese | Delivered |
| DEMO-009 | High risk, address change blocked | English | Pending |
| DEMO-010 | Missing items, easy auto-refund case | Vietnamese | Delivered |
| DEMO-011 | Refund pending review, medium risk | English | Delivered |
| DEMO-012 | Vietnamese customer, address change allowed | Vietnamese | Processing |
| DEMO-013 | Customer claims not received, medium risk | English | Delivered |
| DEMO-014 | Shipped Vietnamese order | Vietnamese | Shipped |
| DEMO-015 | Payment failed, pending resolution | English | Pending |

**Test Query Categories:**
- `order_status`: Order tracking and status inquiries
- `refund`: Refund requests (damaged, wrong item, missing, not received)
- `address_change`: Shipping address update requests
- `policy_question`: Policy inquiries (refund policy, shipping, evidence requirements)
- `demo`: Queries specifically for demo orders
- `edge_case`: Edge cases (incomplete queries, missing order IDs, emotional language)

---

## Testing

### Run All Tests

```bash
# Run full test suite
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
uv run pytest tests/ -v

# Property-based tests
uv run pytest tests/property/ -v

# Integration tests
uv run pytest tests/test_graph_flows.py -v

# Week 3 enhancement tests
uv run pytest tests/test_week3_enhancements.py -v
```

### Run Single Test File

```bash
# Test refund service
uv run pytest tests/test_refunds_service.py -v

# Test API endpoints
uv run pytest tests/test_api.py -v
```

### Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit Tests | `tests/test_*.py` | Test individual functions and classes |
| Property Tests | `tests/property/` | Hypothesis-based property testing |
| Integration Tests | `tests/test_graph_flows.py` | End-to-end workflow tests |
| Enhancement Tests | `tests/test_week3_enhancements.py` | Week 3 feature tests |

### Example Test Commands

```bash
# Run tests matching pattern
uv run pytest -k "refund" -v

# Run tests with specific marker
uv run pytest -m "asyncio" -v

# Stop on first failure
uv run pytest -x

# Run tests in parallel
uv run pytest -n auto
```

---

## Project Structure

```
resolveai/
├── app/                          # Application source code
│   ├── main.py                   # FastAPI application entry point
│   ├── agent/                    # LangGraph agent implementation
│   │   ├── graph.py              # Graph definition and routing
│   │   ├── nodes.py              # Node implementations
│   │   ├── state.py              # State schema
│   │   ├── llm.py                # LLM integration
│   │   └── prompts.py            # Prompt templates
│   ├── api/                      # API routes
│   │   └── routes.py             # Endpoint definitions
│   ├── core/                     # Core utilities
│   │   ├── config.py             # Settings and configuration
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── validation.py         # Validation utilities
│   │   ├── logging.py            # Structured logging
│   │   ├── metrics.py            # Prometheus metrics
│   │   ├── tracing.py            # LangSmith tracing
│   │   └── circuit_breaker.py    # Fault tolerance
│   ├── data/                     # Database layer
│   │   ├── db.py                 # Database connection
│   │   ├── async_db.py           # Async database support
│   │   ├── models.py             # SQLAlchemy models
│   │   └── seed.py               # Data seeding
│   ├── middleware/               # Middleware components
│   │   ├── rate_limit.py         # Rate limiting
│   │   ├── correlation.py        # Correlation IDs
│   │   ├── logging.py            # Request logging
│   │   └── prometheus.py         # Metrics middleware
│   ├── services/                 # Business logic
│   │   ├── analytics.py          # Analytics service
│   │   ├── cache.py              # Caching service
│   │   ├── orders.py             # Order operations
│   │   ├── refunds.py            # Refund processing
│   │   ├── escalations.py        # Escalation handling
│   │   └── retrieval.py          # Vector search
│   └── evals/                    # Evaluation
│       ├── runner.py             # Eval runner
│       ├── ragas_eval.py         # RAGAS metrics
│       └── ragas_pipeline.py     # Eval pipeline
├── ui/                           # Streamlit frontend
│   └── app.py                    # UI application
├── data/                         # Data files
│   ├── knowledge_base/           # Policy documents
│   └── evals/                    # Evaluation data
├── docker/                       # Docker configuration
│   ├── docker-compose.yml        # Development compose
│   ├── docker-compose.prod.yml   # Production compose
│   └── prometheus/               # Prometheus config
├── tests/                        # Test suite
│   ├── conftest.py               # Test fixtures
│   ├── test_*.py                 # Unit tests
│   └── property/                 # Property tests
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # Architecture overview
│   ├── ENHANCEMENT_ROADMAP.md    # Enhancement plan
│   └── WEEK3_IMPLEMENTATION.md   # Week 3 details
├── .env.example                  # Environment template
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependencies
├── Dockerfile                    # Backend container
├── Dockerfile.ui                 # UI container
└── README.md                     # This file
```

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Main conversation endpoint |
| GET | `/health` | Health check |
| GET | `/metrics` | Dashboard metrics |
| GET | `/performance` | Node performance statistics |
| GET | `/escalations` | Recent escalations list |
| GET | `/prometheus` | Prometheus metrics |

### Example Requests

#### Chat Endpoint

```bash
curl -X POST http://localhost:10000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is my order ORD-000001?"}'
```

Response:
```json
{
  "conversation_id": "uuid-here",
  "intent": "order_status",
  "language": "en",
  "response": "Order ORD-000001 is currently processing...",
  "tool_used": "get_order_status",
  "resolved": true,
  "requires_human": false,
  "confidence_score": 0.92
}
```

#### Health Check

```bash
curl http://localhost:10000/health
# Response: {"status": "ok"}
```

---

## Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Production Environment

```bash
# Start production stack
docker-compose -f docker/docker-compose.prod.yml up -d

# Scale API workers
docker-compose -f docker/docker-compose.prod.yml up -d --scale api=3
```

### Monitoring Stack

```bash
# Start with Prometheus and Grafana
docker-compose -f docker/docker-compose.monitoring.yml up -d

# Access Grafana at http://localhost:3000
# Access Prometheus at http://localhost:9090
```

### Docker Environment Variables

Create `docker/.env.docker`:

```bash
DEEPSEEK_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/orders.db
LANGSMITH_API_KEY=your_langsmith_key
OPENAI_API_KEY=your_openai_key
```

---

## Troubleshooting

### Common Issues

#### 1. API Key Errors

**Problem**: `AuthenticationError: Error code: 401`

**Solution**:
- Verify your API keys in `.env` file
- Ensure keys are valid and not expired
- Check that `.env` file is in the project root

```bash
# Verify environment variables are loaded
uv run python -c "from app.core.config import get_settings; print(get_settings().DEEPSEEK_API_KEY)"
```

#### 2. Database Errors

**Problem**: `sqlite3.OperationalError: no such table: orders`

**Solution**:
```bash
# Re-seed the database
uv run python -m app.data.seed
```

#### 3. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in the project root
cd resolveai

# Reinstall dependencies
uv sync
```

#### 4. Port Already in Use

**Problem**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :10000

# Kill process
kill -9 <PID>

# Or use different port
uv run uvicorn app.main:app --port 10001
```

#### 5. FAISS Index Not Found

**Problem**: Vector index not found errors

**Solution**:
```bash
# The index is built automatically on first run
# If issues persist, rebuild:
rm -rf data/vector_index
uv run python -c "from app.services.retrieval import retrieve_policy_context; retrieve_policy_context('test')"
```

#### 6. Test Failures

**Problem**: Tests failing with API errors

**Solution**:
```bash
# Tests should work without API keys (using fallbacks)
# If failing, check conftest.py fixtures
uv run pytest --tb=long -v
```

### Debug Mode

Enable debug logging:

```bash
# Set log level
export LOG_LEVEL=DEBUG
uv run uvicorn app.main:app --reload
```

### Health Check

```bash
# Check all components
curl http://localhost:10000/health
curl http://localhost:10000/metrics
curl http://localhost:10000/performance
```

---

## Contributing

### Development Setup

1. Fork and clone the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Install development dependencies:
   ```bash
   uv sync --all-groups
   ```
4. Make your changes
5. Run tests:
   ```bash
   uv run pytest
   ```
6. Format code:
   ```bash
   uv run ruff format .
   uv run ruff check .
   ```
7. Commit and push:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```
8. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Maintain test coverage above 80%

### Pre-commit Hooks

```bash
# Install pre-commit
uv pip install pre-commit

# Run hooks
pre-commit run --all-files
```

### Adding New Features

1. Create feature in appropriate module under `app/`
2. Add tests in `tests/`
3. Update documentation in `docs/`
4. Update API documentation if adding endpoints

### Reporting Issues

When reporting issues, include:

1. Python version (`python --version`)
2. Operating system
3. Full error message and stack trace
4. Steps to reproduce
5. Expected vs actual behavior

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- [LangChain](https://langchain.com/) for LLM framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) for agent workflows
- [FastAPI](https://fastapi.tiangolo.com/) for API framework
- [Streamlit](https://streamlit.io/) for UI framework
- [FAISS](https://faiss.ai/) for vector search
- [RAGAS](https://docs.ragas.io/) for RAG evaluation
