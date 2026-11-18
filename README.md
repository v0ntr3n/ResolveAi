# ResolveAI

<img src="ui-nextjs/public/favic
on.svg" alt="ResolveAI Logo" width="60" heigh
t="60" align="right">

ResolveAI is a bilingu
al autonomous Tier-1 support system built wit
h LangGraph, FastAPI, and Next.js. It provide
s intelligent customer support for order stat
us inquiries, refund requests, address change
s, and policy questions in both English and V
ietnamese.

## Table of Contents

- [Project 
Overview](#project-overview)
- [RAGAS Evaluat
ion Metrics](#ragas-evaluation-metrics)
- [Pr
erequisites](#prerequisites)
- [Installation]
(#installation)
- [Environment Configuration]
(#environment-configuration)
- [Database Setu
p](#database-setup)
- [Running the Applicatio
n](#running-the-application)
- [Testing](#tes
ting)
- [Project Structure](#project-structur
e)
- [API Endpoints](#api-endpoints)
- [Docke
r Deployment](#docker-deployment)
- [Troubles
hooting](#troubleshooting)
- [Contributing](#
contributing)

---

## 🚀 Quick Start Demo


Get ResolveAI running in under 5 minutes!

#
## 1. Install & Run

```bash
# Clone and inst
all
git clone https://github.com/yourusername
/resolveai.git
cd resolveai
uv sync

# Copy e
nvironment file
cp .env.example .env

# Start
 backend (terminal 1)
uv run uvicorn app.main
:app --reload --port 10000

# Start Next.js U
I (terminal 2)
cd ui-nextjs && npm install &&
 npm run dev
```

### 2. Try Demo Queries

Op
en the UI at http://localhost:3000 and try th
ese queries:

| Query | Expected Response |
|
-------|-------------------|
| `Where is my o
rder DEMO-001?` | Order status: delivered |
|
 `I want a refund for order DEMO-002` | Reque
sts photo evidence |
| `Change address for DE
MO-003 to 123 New St` | Address updated succe
ssfully |
| `What is your return policy?` | P
olicy from knowledge base |
| `Tôi muốn đ
ổi địa chỉ cho DEMO-012` | Vietnamese 
address change |

### 3. Demo Screenshots

##
## Dashboard & Chat Interface
![ResolveAI Das
hboard Light](images/demo_dashboard_light.png
)
![ResolveAI Dashboard Dark](images/demo_das
hboard_dark.png)

#### Live Demo
![ResolveAI 
Demo](images/demo.gif)

The modern Next.js UI
 features:
- **Bento Grid Layout**: Asymmetri
c dashboard with smooth animations
- **Real-t
ime Chat**: Interactive chat with typing indi
cators
- **Demo Orders Panel**: Quick access 
to test scenarios
- **Quick Actions**: One-cl
ick buttons for common tasks

### Demo Order 
Scenarios

The system includes 15 pre-configu
red demo orders for testing:

| Order ID | Sc
enario | Test With |
|----------|----------|-
----------|
| DEMO-001 | Standard delivered o
rder | `"Where is order DEMO-001?"` |
| DEMO-
002 | Damaged item, needs evidence | `"Refund
 DEMO-002, it's damaged"` |
| DEMO-003 | Pend
ing, address change allowed | `"Change addres
s for DEMO-003"` |
| DEMO-008 | High value (>
$120) | `"I want a refund for DEMO-008"` |
| 
DEMO-012 | Vietnamese customer | `"Đổi đ�
��a chỉ cho DEMO-012"` |

---

## Project O
verview

### Purpose

ResolveAI demonstrates 
a production-ready RAG (Retrieval-Augmented G
eneration) system for customer support automa
tion. It showcases:

- **Intelligent Intent C
lassification**: LLM-powered with rule-based 
fallback
- **Semantic Search**: FAISS-based v
ector search for policy documents
- **Multi-L
ayer Caching**: LRU caches for orders, polici
es, and metrics
- **Robust Error Handling**: 
Custom exceptions, validation utilities, and 
circuit breakers
- **API Rate Limiting**: Pro
tection against abuse with configurable limit
s
- **Performance Monitoring**: Real-time tra
cking with Prometheus metrics
- **Distributed
 Tracing**: LangSmith integration for workflo
w visibility
- **RAG Quality Evaluation**: RA
GAS metrics for response quality assessment


### System Architecture

```mermaid
flowchart LR
    U["Customer (EN / VI)"] --> UI["Next.js Frontend"]
    UI --> API["FastAPI Backend"]
    API --> G["LangGraph Orchestrator"]
    G --> IC["Intent Classifier & Guardrails"]
    IC -->|Policy Q&A| RAG["Intent-Routed FAISS RAG + Reranker"]
    IC -->|Order / Address / Refund| DB[("SQLite / PostgreSQL")]
    IC -->|High-Value / Risky| ESC["Human Escalation Queue"]
    RAG --> EVAL["RAGAS Evaluation (0.773 Faithfulness)"]
```

### Supported Operations

| Operation | Descr
iption | Guardrails |
|-----------|----------
---|------------|
| Order Status | Track orde
r location and delivery status | None |
| Ref
und Processing | Handle refund requests | Amo
unt > $50 requires human approval |
| Address
 Change | Update shipping address | Only befo
re shipment, not for risky orders |
| Policy 
Q&A | Answer policy questions | Semantic sear
ch with context |
| Evidence Handling | Reque
st evidence for damaged items | Photo require
d for damaged/wrong-item claims |

### Langua
ge Support

- **English**: Full support for a
ll operations
- **Vietnamese**: Full support 
for all operations

### RAGAS Evaluation Metr
ics

ResolveAI uses RAGAS (Retrieval Augmente
d Generation Assessment) to evaluate the qual
ity of RAG responses. The evaluation measures
 four key metrics:

| Metric | Description | 
Current Score |
|--------|-------------|-----
----------|
| **Overall Score** | Combined sc
ore across all metrics | 0.659 |
| **Faithful
ness** | How well the answer is grounded in r
etrieved context | 0.773 |
| **Answer Relevan
cy** | How relevant the answer is to the ques
tion | 0.788 |
| **Context Precision** | How 
relevant the retrieved context is | 0.350 |
|
 **Context Recall** | How well the context co
vers the expected answer | 0.725 |

#### Rece
nt Improvements

The RAG system has been opti
mized with the following enhancements:

- **I
ntent-Based Document Routing**: Query intent 
detection for better document retrieval
- **R
eranking Implementation**: Prioritizes releva
nt chunks from target policy files
- **Higher
 Relevance Threshold**: Increased from 0.3 to
 0.4 for better precision
- **Per-Chunk Sourc
e Tracking**: Accurate source attribution for
 reranking

To run the RAGAS evaluation:

```
bash
uv run python -m app.evals.ragas_pipelin
e
```

Evaluation reports are saved to `data/
evals/ragas_report.json`.

---

## Prerequisi
tes

### System Requirements

- **Python**: 3
.12 or higher
- **Operating System**: Windows
, macOS, or Linux
- **Memory**: Minimum 4GB R
AM (8GB recommended)
- **Disk Space**: 1GB fo
r application + data

### Required Software


- **uv**: Fast Python package installer (reco
mmended)
  ```bash
  # Install uv
  pip insta
ll uv
  ```

- **Git**: For cloning the repos
itory
  ```bash
  # Verify git installation
 
 git --version
  ```

### Optional (for Docke
r deployment)

- **Docker**: 20.10 or higher

- **Docker Compose**: 2.0 or higher

---

## 
Installation

### Step 1: Clone the Repositor
y

```bash
git clone https://github.com/youru
sername/resolveai.git
cd resolveai
```

### S
tep 2: Create Virtual Environment and Install
 Dependencies

Using uv (recommended):
```bas
h
# Create virtual environment and install de
pendencies
uv sync

# Or install with dev dep
endencies
uv sync --all-groups
```

Using pip
 (alternative):
```bash
# Create virtual envi
ronment
python -m venv .venv

# Activate virt
ual environment
# On Windows:
.venv\Scripts\a
ctivate
# On macOS/Linux:
source .venv/bin/ac
tivate

# Install dependencies
pip install -r
 requirements.txt
```

### Step 3: Configure 
Environment Variables

```bash
# Copy example
 environment file
cp .env.example .env

# Edi
t .env with your API keys
# See Environment C
onfiguration section for details
```

### Ste
p 4: Initialize Data

```bash
# Seed the data
base with sample orders
uv run python -m app.
data.seed
```

---

## Environment Configurat
ion

### Required Environment Variables

Crea
te a `.env` file in the project root with the
 following variables:

```bash
# Core Configu
ration
DEEPSEEK_API_KEY=your_deepseek_api_key
_here
DEEPSEEK_MODEL=deepseek-chat
DATABASE_U
RL=sqlite:///./data/orders.db
VECTOR_INDEX_DI
R=./data/vector_index
AUTO_SEED_DATA=true
REF
UND_APPROVAL_THRESHOLD=50.0
```

### Optional
 Environment Variables

#### LangSmith Tracin
g (for workflow visibility)

```bash
LANGSMIT
H_API_KEY=your_langsmith_key_here
LANGSMITH_P
ROJECT=resolveai-production
LANGSMITH_ORG=you
r_org_id
```

#### RAGAS Evaluation (for RAG 
quality metrics)

```bash
OPENAI_API_KEY=your
_openai_key_here
```

#### Prometheus Metrics


```bash
PROMETHEUS_ENABLED=true
METRICS_POR
T=9090
```

### Obtaining API Keys

| Service
 | Purpose | How to Obtain |
|---------|-----
----|---------------|
| DeepSeek | LLM for in
tent classification and responses | [DeepSeek
 Platform](https://platform.deepseek.com/) |

| LangSmith | Distributed tracing for LLM wor
kflows | [LangSmith](https://smith.langchain.
com/) |
| OpenAI | RAGAS evaluation metrics |
 [OpenAI Platform](https://platform.openai.co
m/) |

---

## Database Setup

### SQLite (De
fault)

The default configuration uses SQLite
, which requires no additional setup:

```bas
h
# Database is automatically created at data
/orders.db
# Seed initial data:
uv run python
 -m app.data.seed
```

### PostgreSQL (Produc
tion)

For production, use PostgreSQL:

1. In
stall PostgreSQL and create a database:
   ``
`bash
   createdb resolveai
   ```

2. Update
 `DATABASE_URL` in `.env`:
   ```bash
   DATA
BASE_URL=postgresql://user:password@localhost
:5432/resolveai
   ```

3. Run migrations:
  
 ```bash
   uv run python -m app.data.seed
  
 ```

### Database Schema

The database conta
ins three main tables:

- **orders**: Custome
r orders with status, tracking, and refund in
formation
- **escalations**: Human interventi
on requests
- **conversation_logs**: Conversa
tion history and analytics

---

## Running t
he Application

### Development Mode

#### St
art Backend API

```bash
# Using uvicorn with
 auto-reload
uv run uvicorn app.main:app --re
load --host 0.0.0.0 --port 10000
```

#### St
art Next.js UI

```bash
# In a separate termi
nal
cd ui-nextjs && npm install && npm run de
v
```

#### Access the Application

- **API**
: http://localhost:10000
- **API Documentatio
n**: http://localhost:10000/docs
- **Next.js 
UI**: http://localhost:3000

### Production M
ode

#### Using Gunicorn

```bash
# Install g
unicorn
uv pip install gunicorn

# Run with m
ultiple workers
uv run gunicorn app.main:app 
-w 4 -k uvicorn.workers.UvicornWorker -b 0.0.
0.0:10000
```

#### Using Docker

See [Docker
 Deployment](#docker-deployment) section.

##
# Demo Scripts

Windows PowerShell:
```powers
hell
# Run smoke test
powershell -ExecutionPo
licy Bypass -File scripts/demo_smoke.ps1

# S
eed demo orders for testing
powershell -Execu
tionPolicy Bypass -File scripts/seed_demo.ps1

```

### Demo Orders

The project includes p
redefined demo orders for testing various sce
narios:

```bash
# Seed demo orders (15 order
s with various test scenarios)
uv run python 
-m app.data.seed_demo
```

**Demo Order Scena
rios:**

| Order ID | Scenario | Language | S
tatus |
|----------|----------|----------|---
-----|
| DEMO-001 | Standard delivered, refun
d eligible | English | Delivered |
| DEMO-002
 | Damaged fragile item, needs photo evidence
 | Vietnamese | Delivered |
| DEMO-003 | Pend
ing order, address change allowed | English |
 Pending |
| DEMO-004 | Processing, special h
andling, medium risk | Vietnamese | Processin
g |
| DEMO-005 | Shipped, cannot change addre
ss | English | Shipped |
| DEMO-006 | Refund 
already approved (wrong item) | Vietnamese | 
Delivered |
| DEMO-007 | Out for delivery, fr
agile | English | Out for Delivery |
| DEMO-0
08 | High value (>$120), NOT auto-refund elig
ible | Vietnamese | Delivered |
| DEMO-009 | 
High risk, address change blocked | English |
 Pending |
| DEMO-010 | Missing items, easy a
uto-refund case | Vietnamese | Delivered |
| 
DEMO-011 | Refund pending review, medium risk
 | English | Delivered |
| DEMO-012 | Vietnam
ese customer, address change allowed | Vietna
mese | Processing |
| DEMO-013 | Customer cla
ims not received, medium risk | English | Del
ivered |
| DEMO-014 | Shipped Vietnamese orde
r | Vietnamese | Shipped |
| DEMO-015 | Payme
nt failed, pending resolution | English | Pen
ding |

**Test Query Categories:**
- `order_s
tatus`: Order tracking and status inquiries
-
 `refund`: Refund requests (damaged, wrong it
em, missing, not received)
- `address_change`
: Shipping address update requests
- `policy_
question`: Policy inquiries (refund policy, s
hipping, evidence requirements)
- `demo`: Que
ries specifically for demo orders
- `edge_cas
e`: Edge cases (incomplete queries, missing o
rder IDs, emotional language)

---

## Testin
g

### Run All Tests

```bash
# Run full test
 suite
uv run pytest

# Run with verbose outp
ut
uv run pytest -v

# Run with coverage
uv r
un pytest --cov=app --cov-report=html
```

##
# Run Specific Test Categories

```bash
# Uni
t tests only
uv run pytest tests/ -v

# Prope
rty-based tests
uv run pytest tests/property/
 -v

# Integration tests
uv run pytest tests/
test_graph_flows.py -v

# Week 3 enhancement 
tests
uv run pytest tests/test_week3_enhancem
ents.py -v
```

### Run Single Test File

```
bash
# Test refund service
uv run pytest test
s/test_refunds_service.py -v

# Test API endp
oints
uv run pytest tests/test_api.py -v
```


### Test Categories

| Category | Location |
 Purpose |
|----------|----------|---------|

| Unit Tests | `tests/test_*.py` | Test indiv
idual functions and classes |
| Property Test
s | `tests/property/` | Hypothesis-based prop
erty testing |
| Integration Tests | `tests/t
est_graph_flows.py` | End-to-end workflow tes
ts |
| Enhancement Tests | `tests/test_week3_
enhancements.py` | Week 3 feature tests |

##
# Example Test Commands

```bash
# Run tests 
matching pattern
uv run pytest -k "refund" -v


# Run tests with specific marker
uv run pyt
est -m "asyncio" -v

# Stop on first failure

uv run pytest -x

# Run tests in parallel
uv 
run pytest -n auto
```

---

## Project Struc
ture

```
resolveai/
├── app/          
                # Application source code
│
   ├── main.py                   # Fast
API application entry point
│   ├── a
gent/                    # LangGraph agent im
plementation
│   │   ├── graph.py  
            # Graph definition and routing
�
�   │   ├── nodes.py              # N
ode implementations
│   │   ├── sta
te.py              # State schema
│   │  
 ├── llm.py                # LLM integr
ation
│   │   └── prompts.py       
     # Prompt templates
│   ├── api/ 
                     # API routes
│   │  
 └── routes.py             # Endpoint d
efinitions
│   ├── core/             
        # Core utilities
│   │   ├─�
� config.py             # Settings and config
uration
│   │   ├── exceptions.py  
       # Custom exceptions
│   │   ├─
─ validation.py         # Validation utilit
ies
│   │   ├── logging.py         
   # Structured logging
│   │   ├──
 metrics.py            # Prometheus metrics
�
��   │   ├── tracing.py            # 
LangSmith tracing
│   │   └── circu
it_breaker.py    # Fault tolerance
│   ├�
��─ data/                     # Database la
yer
│   │   ├── db.py              
   # Database connection
│   │   ├─�
� async_db.py           # Async database supp
ort
│   │   ├── models.py          
   # SQLAlchemy models
│   │   └── 
seed.py               # Data seeding
│   �
�── middleware/               # Middlewar
e components
│   │   ├── rate_limit
.py         # Rate limiting
│   │   ├�
�─ correlation.py        # Correlation IDs

│   │   ├── logging.py            #
 Request logging
│   │   └── promet
heus.py         # Metrics middleware
│   �
�── services/                 # Business 
logic
│   │   ├── analytics.py     
     # Analytics service
│   │   ├─�
� cache.py              # Caching service
│
   │   ├── orders.py             # Or
der operations
│   │   ├── refunds.
py            # Refund processing
│   │  
 ├── escalations.py        # Escalation
 handling
│   │   └── retrieval.py 
         # Vector search
│   └── eval
s/                    # Evaluation
│       
├── runner.py             # Eval runner

│       ├── ragas_eval.py         # 
RAGAS metrics
│       └── ragas_pipel
ine.py     # Eval pipeline
├── ui-nextj
s/                    # Next.js frontend
│ 
  ├── app/                      # Next.
js app directory
│   ├── components/ 
              # React components
│   └─
─ public/                   # Static assets

├── data/                         # Da
ta files
│   ├── knowledge_base/     
      # Policy documents
│   └── eval
s/                    # Evaluation data
├�
�─ docker/                       # Docker c
onfiguration
│   ├── docker-compose.y
ml        # Development compose
│   ├─�
�� docker-compose.prod.yml   # Production com
pose
│   └── prometheus/             
  # Prometheus config
├── tests/       
                 # Test suite
│   ├──
 conftest.py               # Test fixtures
�
�   ├── test_*.py                 # Uni
t tests
│   └── property/            
     # Property tests
├── docs/        
                 # Documentation
│   ├─
─ ARCHITECTURE.md           # Architecture 
overview
│   ├── ENHANCEMENT_ROADMAP.
md    # Enhancement plan
│   └── WEEK
3_IMPLEMENTATION.md   # Week 3 details
├─
─ .env.example                  # Environme
nt template
├── pyproject.toml         
       # Project configuration
├── requ
irements.txt              # Dependencies
├�
��─ Dockerfile                    # Backend
 container
├── Dockerfile.nextjs       
      # Next.js container
└── README.md
                     # This file
```

---

##
 API Endpoints

### Core Endpoints

| Method 
| Endpoint | Description |
|--------|--------
--|-------------|
| POST | `/chat` | Main con
versation endpoint |
| GET | `/health` | Heal
th check |
| GET | `/metrics` | Dashboard met
rics |
| GET | `/performance` | Node performa
nce statistics |
| GET | `/escalations` | Rec
ent escalations list |
| GET | `/prometheus` 
| Prometheus metrics |

### Example Requests


#### Chat Endpoint

```bash
curl -X POST htt
p://localhost:10000/chat \
  -H "Content-Type
: application/json" \
  -d '{"message": "Wher
e is my order ORD-000001?"}'
```

Response:
`
``json
{
  "conversation_id": "uuid-here",
  
"intent": "order_status",
  "language": "en",

  "response": "Order ORD-000001 is currently
 processing...",
  "tool_used": "get_order_st
atus",
  "resolved": true,
  "requires_human"
: false,
  "confidence_score": 0.92
}
```

##
## Health Check

```bash
curl http://localhos
t:10000/health
# Response: {"status": "ok"}
`
``

---

## Docker Deployment

### Developmen
t Environment

```bash
# Start all services
d
ocker-compose -f docker/docker-compose.yml up
 -d

# View logs
docker-compose -f docker/doc
ker-compose.yml logs -f

# Stop services
dock
er-compose -f docker/docker-compose.yml down

```

### Production Environment

```bash
# St
art production stack
docker-compose -f docker
/docker-compose.prod.yml up -d

# Scale API w
orkers
docker-compose -f docker/docker-compos
e.prod.yml up -d --scale api=3
```

### Monit
oring Stack

```bash
# Start with Prometheus 
and Grafana
docker-compose -f docker/docker-c
ompose.monitoring.yml up -d

# Access Grafana
 at http://localhost:3000
# Access Prometheus
 at http://localhost:9090
```

### Docker Env
ironment Variables

Create `docker/.env.docke
r`:

```bash
DEEPSEEK_API_KEY=your_key_here
D
ATABASE_URL=sqlite:///./data/orders.db
LANGSM
ITH_API_KEY=your_langsmith_key
OPENAI_API_KEY
=your_openai_key
```

---

## Troubleshooting


### Common Issues

#### 1. API Key Errors


**Problem**: `AuthenticationError: Error code
: 401`

**Solution**:
- Verify your API keys 
in `.env` file
- Ensure keys are valid and no
t expired
- Check that `.env` file is in the 
project root

```bash
# Verify environment va
riables are loaded
uv run python -c "from app
.core.config import get_settings; print(get_s
ettings().DEEPSEEK_API_KEY)"
```

#### 2. Dat
abase Errors

**Problem**: `sqlite3.Operation
alError: no such table: orders`

**Solution**
:
```bash
# Re-seed the database
uv run pytho
n -m app.data.seed
```

#### 3. Import Errors


**Problem**: `ModuleNotFoundError: No modul
e named 'app'`

**Solution**:
```bash
# Ensur
e you're in the project root
cd resolveai

# 
Reinstall dependencies
uv sync
```

#### 4. P
ort Already in Use

**Problem**: `OSError: [E
rrno 98] Address already in use`

**Solution*
*:
```bash
# Find process using port
lsof -i 
:10000

# Kill process
kill -9 <PID>

# Or us
e different port
uv run uvicorn app.main:app 
--port 10001
```

#### 5. FAISS Index Not Fou
nd

**Problem**: Vector index not found error
s

**Solution**:
```bash
# The index is built
 automatically on first run
# If issues persi
st, rebuild:
rm -rf data/vector_index
uv run 
python -c "from app.services.retrieval import
 retrieve_policy_context; retrieve_policy_con
text('test')"
```

#### 6. Test Failures

**P
roblem**: Tests failing with API errors

**So
lution**:
```bash
# Tests should work without
 API keys (using fallbacks)
# If failing, che
ck conftest.py fixtures
uv run pytest --tb=lo
ng -v
```

### Debug Mode

Enable debug loggi
ng:

```bash
# Set log level
export LOG_LEVEL
=DEBUG
uv run uvicorn app.main:app --reload
`
``

### Health Check

```bash
# Check all com
ponents
curl http://localhost:10000/health
cu
rl http://localhost:10000/metrics
curl http:/
/localhost:10000/performance
```

---

## Con
tributing

### Development Setup

1. Fork and
 clone the repository
2. Create a feature bra
nch:
   ```bash
   git checkout -b feature/yo
ur-feature-name
   ```
3. Install development
 dependencies:
   ```bash
   uv sync --all-gr
oups
   ```
4. Make your changes
5. Run tests
:
   ```bash
   uv run pytest
   ```
6. Forma
t code:
   ```bash
   uv run ruff format .
  
 uv run ruff check .
   ```
7. Commit and pus
h:
   ```bash
   git add .
   git commit -m "
feat: your feature description"
   git push o
rigin feature/your-feature-name
   ```
8. Ope
n a Pull Request

### Code Style

- Follow PE
P 8 guidelines
- Use type hints for all funct
ions
- Write docstrings for public functions

- Maintain test coverage above 80%

### Pre-c
ommit Hooks

```bash
# Install pre-commit
uv 
pip install pre-commit

# Run hooks
pre-commi
t run --all-files
```

### Adding New Feature
s

1. Create feature in appropriate module un
der `app/`
2. Add tests in `tests/`
3. Update
 documentation in `docs/`
4. Update API docum
entation if adding endpoints

### Reporting I
ssues

When reporting issues, include:

1. Py
thon version (`python --version`)
2. Operatin
g system
3. Full error message and stack trac
e
4. Steps to reproduce
5. Expected vs actual
 behavior

---

## License

This project is l
icensed under the MIT License - see the LICEN
SE file for details.

---

## Acknowledgments


- [LangChain](https://langchain.com/) for L
LM framework
- [LangGraph](https://langchain-
ai.github.io/langgraph/) for agent workflows

- [FastAPI](https://fastapi.tiangolo.com/) fo
r API framework
- [Streamlit](https://streaml
it.io/) for UI framework
- [FAISS](https://fa
iss.ai/) for vector search
- [RAGAS](https://
docs.ragas.io/) for RAG evaluation


