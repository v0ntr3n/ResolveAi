# ResolveAI Design

## Summary

ResolveAI is a bilingual Tier-1 support agent for e-commerce operations. It handles order status lookup, refund requests, shipping address changes, and policy questions in English and Vietnamese. The system is optimized for portfolio use: fast to run locally, easy to demo, and structured enough to discuss as a real production-oriented agent.

## Product Goal

Build a working autonomous support agent that can:

- answer policy questions with retrieval-augmented generation
- identify support intent from natural language
- query a mock order database
- update shipping addresses when policy allows
- process low-value refunds automatically
- escalate risky or ambiguous cases to a human queue

The project should be demonstrable end-to-end from a local machine with a single repository.

## Scope

### Included

- English and Vietnamese chat support
- Order status workflow
- Refund workflow
- Shipping address change workflow
- Policy question answering from local knowledge base files
- Human escalation queue for sensitive or failed actions
- Structured conversation logs and product metrics
- FastAPI backend API
- Streamlit chat UI and lightweight admin dashboard
- Local SQLite database with synthetic orders
- Mock refund provider service
- LangGraph-based orchestration

### Excluded From First Version

- Real payment processor integration
- Real CRM, ticketing, or Jira integration
- File upload for new knowledge base content
- Authenticated multi-user accounts
- Production-grade RBAC
- Full evaluation harness or load testing framework

## User Flows

### 1. Order Status

1. User asks where their order is.
2. Agent extracts order identifier or asks for it.
3. Agent reads the order from SQLite.
4. Agent returns status, tracking number, and next expected step.
5. System logs the resolution outcome.

### 2. Refund Request

1. User asks for a refund.
2. Agent identifies the order and checks refund eligibility.
3. Agent reads order amount and policy constraints.
4. If amount is `<= 50 USD` and the order is eligible, the agent calls the mock refund tool.
5. If amount is `> 50 USD`, the agent creates an escalation record instead of refunding.
6. Agent confirms the result to the user in the user’s language.

### 3. Shipping Address Change

1. User requests an address change.
2. Agent identifies the order and collects the new address.
3. Agent checks whether the order is still modifiable.
4. If status is pre-shipment, the system updates the record automatically.
5. If status is already shipped or delivered, the request is escalated.
6. Agent explains the result clearly.

### 4. Policy Questions

1. User asks about returns, shipping, or support rules.
2. Agent retrieves relevant local policy snippets.
3. Agent answers in English or Vietnamese and cites the policy source title.

## Core Safety Rules

- Refunds above `50 USD` always require human review.
- Address changes are allowed only for pre-shipment orders.
- Missing order identity blocks action execution.
- Two consecutive tool failures trigger escalation.
- Low model confidence triggers escalation.
- Detected user frustration triggers escalation with a summary.
- All financial or record-changing actions must produce a structured audit log.

## Bilingual Behavior

- The system detects whether the user is speaking English or Vietnamese.
- Responses should default to the language of the latest user message.
- Policy files are stored in bilingual form with equivalent rules in both languages.
- Logs store detected language for downstream analysis.

## Architecture

### Backend

- `FastAPI` serves chat, metrics, approval queue, and health endpoints.
- A service layer owns database access, policy retrieval, mock refund execution, and analytics logging.
- The LangGraph agent runs inside the backend and exposes a simple callable interface to the API layer.

### Agent

The graph uses explicit state and conditional routing:

1. `classify_intent`
2. `retrieve_policy_context`
3. `resolve_order_context`
4. `decide_action`
5. `execute_tool`
6. `escalate_if_needed`
7. `compose_response`
8. `write_conversation_log`

The graph should favor deterministic checks for safety-critical conditions instead of relying only on model judgment.

### Data

- `SQLite` stores synthetic orders and escalation records.
- Local Markdown files provide policy knowledge.
- A lightweight local vector index stores policy chunks for retrieval.
- JSON files store eval prompts and optional demo seeds.

### Frontend

- `Streamlit` provides a chat interface, action/result display, and an admin sidebar.
- The sidebar shows recent tool calls, confidence, escalation status, and aggregate metrics.
- The UI should be simple and demo-friendly instead of heavily customized.

## Data Model

### Orders

Fields:

- `order_id`
- `customer_email`
- `customer_name`
- `language_preference`
- `status`
- `tracking_number`
- `created_at`
- `updated_at`
- `amount`
- `currency`
- `payment_status`
- `refund_status`
- `refund_eligible`
- `shipping_address`

### Escalations

Fields:

- `id`
- `order_id`
- `intent`
- `reason`
- `status`
- `created_at`
- `conversation_summary`

### Analytics Logs

Fields:

- `conversation_id`
- `user_message`
- `detected_language`
- `intent`
- `resolved`
- `tool_used`
- `confidence_score`
- `human_intervention_required`
- `latency_ms`
- `created_at`

## Knowledge Base Structure

Store local files under `data/knowledge_base/`:

- `return_policy.md`
- `shipping_policy.md`
- `address_change_policy.md`
- `escalation_policy.md`

Each file contains:

- `## English`
- `## Vietnamese`

The wording should be fictional and original, inspired by real support operations but not copied from third-party help centers.

## Product Metrics

The dashboard should compute:

- deflection rate
- autonomous resolution rate
- escalation rate
- refund auto-approval rate
- average handle time
- tool failure count

For the MVP, these metrics can be derived from local analytics logs.

## Demo Readiness Requirements

- Start backend locally with one command.
- Start Streamlit UI locally with one command.
- Seed the database with synthetic orders automatically.
- Include at least 20 test prompts covering safe, unsafe, and bilingual cases.
- Show at least one approval-queue case in the demo.
- Provide clear README setup instructions.

## Testing Strategy

- Unit tests for order service, refund rules, address change rules, and policy retrieval.
- Integration tests for main agent flows using deterministic fixtures.
- Smoke tests for API endpoints.
- No dependency on external live services during tests.

## Risks And Mitigations

### Risk: LLM output inconsistency

Mitigation:

- use deterministic routing checks where possible
- validate tool inputs before execution
- gate risky actions with rule-based conditions

### Risk: Bilingual ambiguity

Mitigation:

- keep policies aligned across languages
- store language preference in logs
- use simple localized templates for confirmations

### Risk: Weak portfolio signal

Mitigation:

- keep architecture modular
- expose logs and metrics visibly
- document guardrails and escalation logic clearly

## Success Criteria

The first version is complete when:

- the agent resolves order status, refund, and address change requests locally
- refund escalation for values above `50 USD` works reliably
- English and Vietnamese prompts both work
- the dashboard shows structured metrics from actual conversations
- the repo is easy to run and explain in an interview
