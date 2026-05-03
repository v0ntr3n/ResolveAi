# ResolveAI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portfolio-grade bilingual support agent that resolves order status, refund, address change, and policy questions with clear safety guardrails.

**Architecture:** A FastAPI backend hosts the LangGraph agent, services, and metrics endpoints. A Streamlit frontend acts as the chat and admin surface. Local SQLite, Markdown policies, and a lightweight vector index keep the system easy to run and demo.

**Tech Stack:** Python, FastAPI, Streamlit, LangGraph, LangChain, SQLAlchemy, SQLite, FAISS or Chroma, Faker, pytest

---

### Task 1: Repository Skeleton

**Files:**
- Create: `app/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/agent/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/data/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/schemas/__init__.py`
- Create: `ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `README.md`

- [ ] Create the package layout and dependency manifest.
- [ ] Define environment variables for `DEEPSEEK_API_KEY`, database path, and index path.
- [ ] Write a short README with setup, seed, backend, and UI commands.

### Task 2: Configuration And Settings

**Files:**
- Create: `app/core/config.py`
- Create: `tests/test_config.py`

- [ ] Add a `Settings` class using environment-driven configuration.
- [ ] Cover default paths and required API settings with unit tests.
- [ ] Verify settings load without a `.env` file during tests.

### Task 3: Database Models And Session

**Files:**
- Create: `app/data/db.py`
- Create: `app/data/models.py`
- Create: `tests/test_models.py`

- [ ] Define SQLAlchemy models for `Order`, `Escalation`, and `ConversationLog`.
- [ ] Implement session factory and database initialization helpers.
- [ ] Add tests that create the schema in a temporary SQLite database.

### Task 4: Seed Data And Synthetic Orders

**Files:**
- Create: `app/data/seed.py`
- Create: `data/evals/test_queries.json`
- Create: `tests/test_seed.py`

- [ ] Generate 1,000 realistic synthetic orders with English/Vietnamese preferences.
- [ ] Write deterministic seed logic for repeatable local demos.
- [ ] Add tests for row counts and required fields.

### Task 5: Bilingual Policy Pack

**Files:**
- Create: `data/knowledge_base/return_policy.md`
- Create: `data/knowledge_base/shipping_policy.md`
- Create: `data/knowledge_base/address_change_policy.md`
- Create: `data/knowledge_base/escalation_policy.md`
- Create: `tests/test_policy_files.py`

- [ ] Write fictional original policy documents with both English and Vietnamese sections.
- [ ] Ensure business rules match the agent guardrails exactly.
- [ ] Add tests that verify all required sections exist.

### Task 6: Retrieval Layer

**Files:**
- Create: `app/services/retrieval.py`
- Create: `tests/test_retrieval.py`

- [ ] Implement local policy loading and chunking.
- [ ] Build a lightweight vector or keyword retrieval interface for local use.
- [ ] Add tests that retrieve the correct policy for refund and address questions.

### Task 7: Order Service

**Files:**
- Create: `app/services/orders.py`
- Create: `tests/test_orders_service.py`

- [ ] Implement order lookup by order ID.
- [ ] Implement status summary formatting inputs.
- [ ] Implement address update with pre-shipment rule enforcement.
- [ ] Add tests for valid updates and blocked shipped orders.

### Task 8: Refund Service

**Files:**
- Create: `app/services/refunds.py`
- Create: `tests/test_refunds_service.py`

- [ ] Implement refund eligibility checks.
- [ ] Implement mock refund processing for orders at or below `50 USD`.
- [ ] Return escalation reasons for higher-value refunds or invalid states.
- [ ] Add tests for success, ineligible refund, and escalation threshold cases.

### Task 9: Escalation And Analytics Services

**Files:**
- Create: `app/services/escalations.py`
- Create: `app/services/analytics.py`
- Create: `tests/test_escalations_service.py`
- Create: `tests/test_analytics_service.py`

- [ ] Implement escalation record creation and listing.
- [ ] Implement structured conversation log writes.
- [ ] Implement metric aggregation for the dashboard.
- [ ] Add tests for log writes and summary metrics.

### Task 10: LLM And Prompt Layer

**Files:**
- Create: `app/agent/llm.py`
- Create: `app/agent/prompts.py`
- Create: `tests/test_prompts.py`

- [ ] Implement a provider wrapper for DeepSeek chat completion access.
- [ ] Keep the interface swappable for later OpenAI or Groq support.
- [ ] Define prompts for intent classification, language detection, response synthesis, and frustration detection.
- [ ] Add tests for prompt-template rendering and fallback behavior.

### Task 11: LangGraph State And Nodes

**Files:**
- Create: `app/agent/state.py`
- Create: `app/agent/nodes.py`
- Create: `tests/test_agent_nodes.py`

- [ ] Define explicit graph state fields for message, language, intent, order, policy context, confidence, action result, and escalation flags.
- [ ] Implement node functions for classify, retrieve, load order, decide, execute, escalate, respond, and log.
- [ ] Add unit tests for deterministic branching rules.

### Task 12: Graph Assembly

**Files:**
- Create: `app/agent/graph.py`
- Create: `tests/test_graph_flows.py`

- [ ] Assemble the LangGraph workflow with conditional edges.
- [ ] Route policy-only questions away from order tools.
- [ ] Route high-risk refund and blocked address changes into escalation.
- [ ] Add integration tests for:
- [ ] English order status request
- [ ] Vietnamese refund under threshold
- [ ] Refund over threshold requiring escalation
- [ ] Address update blocked after shipment

### Task 13: FastAPI Backend

**Files:**
- Create: `app/api/routes.py`
- Create: `app/main.py`
- Create: `tests/test_api.py`

- [ ] Expose `/health`, `/chat`, `/metrics`, and `/escalations` endpoints.
- [ ] Wire backend startup to schema initialization and optional seeding.
- [ ] Add API tests for health, chat, and metrics responses.

### Task 14: Streamlit UI

**Files:**
- Create: `ui/app.py`
- Create: `tests/test_ui_smoke.py`

- [ ] Build a chat interface that sends requests to the FastAPI backend.
- [ ] Show detected language, tool used, confidence, and escalation status in the sidebar.
- [ ] Show aggregate metrics and recent escalations in an admin view.
- [ ] Add a minimal smoke test for basic UI module import.

### Task 15: Demo Tooling And Documentation

**Files:**
- Modify: `README.md`
- Create: `scripts/run_backend.ps1`
- Create: `scripts/run_ui.ps1`
- Create: `scripts/seed_data.ps1`

- [ ] Add commands for local setup, seeding, backend start, and UI start.
- [ ] Document sample English and Vietnamese prompts.
- [ ] Document the portfolio story: safety rules, LangGraph flow, and metrics.

### Task 16: Verification

**Files:**
- Modify: `README.md`

- [ ] Run the test suite with `pytest`.
- [ ] Run backend smoke checks.
- [ ] Run one manual English conversation and one manual Vietnamese conversation.
- [ ] Confirm logs and metrics update after those conversations.
- [ ] Record any known limitations in the README.
