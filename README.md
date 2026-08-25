# RecoverX — Autonomous AI Revenue Recovery Platform

RecoverX is an enterprise-grade autonomous AI revenue-recovery platform built as a modular monolith in FastAPI/PostgreSQL. It turns failed payment webhooks into deterministic financial truth, extracts explainable revenue intelligence, and deploys a bounded AI agent to reason over and synthesize structured recovery plans.

---

## 🏛️ Architectural Overview & Core Boundaries

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: FINANCIAL EVENT FOUNDATION (Financial Truth)                   │
│ Webhook Ingestion (HMAC-SHA256) → Idempotency → Normalized State        │
│ (Payment, PaymentAttempt, Merchant, Customer) → Recovery Case → Audit   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: REVENUE INTELLIGENCE ENGINE (Deterministic Intelligence)       │
│ Feature Extraction → Failure Classifier → Revenue-at-Risk Calculator    │
│ → Recovery Likelihood Engine → Merchant-Relative Opportunity Scorer     │
│ → Intervention Engine → Persistent revenue_intelligence_results         │
│ (STRICT RULE: NO LLM USED FOR FINANCIAL CALCULATIONS OR SCORING)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: AI RECOVERY AGENT (Bounded AI Reasoning & Planning)            │
│ Read-only Tool Registry → Context Builder → LLM Provider Abstraction    │
│ (Gemini / Groq / OpenAI / Mock) → Structured RecoveryPlan Schema        │
│ → Deterministic PolicyEngine Gate (ALLOWED / BLOCKED / REQUIRES_APPROVAL│
│ → Safe Decision Trace & Persisted agent_runs                            │
│ (STRICT BOUNDARY: PHASE 3 PLANS ACTIONS — EXECUTION STRICTLY DISABLED)  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ (Phase 4 Boundary)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: CONTROLLED ACTION EXECUTION (Future Action Boundary)           │
│ Approved Plan Execution, Automated Smart Retries, Multi-channel Comms   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Architectural Pillars

### 1. Phase 1 — Financial Truth Foundation
- **Webhook HMAC-SHA256 Verification**: Cryptographically verifies incoming provider signatures against raw byte payload with constant-time comparison to prevent timing attacks.
- **Strict Idempotency**: Guarantees that duplicate webhooks (using `x-razorpay-event-id`) never create duplicate records or state transitions.
- **Normalized Domain Models**: Distinct database entities for `Merchant`, `Customer`, `Payment`, `PaymentAttempt`, `RecoveryCase`, and `AuditEvent`.
- **Out-of-Order Resiliency**: Payment state machine allows transition from `FAILED` to `CAPTURED` or `AUTHORIZED` if asynchronous webhooks arrive out of sequence.
- **Merchant Isolation**: All domain queries and audit records enforce merchant tenancy.

### 2. Phase 2 — Deterministic Revenue Intelligence
- **No LLM in Financial Calculations**: Financial scoring, risk calculations, and recovery likelihood are 100% deterministic, testable, reproducible, and explainable.
- **Merchant-Relative Value Normalization**: Instead of arbitrary global thresholds, transaction value is evaluated relative to the merchant's historical distribution (`normalized_value_score`, `transaction_value_percentile`).
- **Bounded Scoring (0-100)**: Opportunity score balances merchant-relative transaction value (40%), recovery likelihood (40%), value percentile (10%), time sensitivity (±10%), and retry context (±15%).
- **Model Versioning**: Every intelligence result records `model_version` (e.g. `rules-v1`) alongside structured contributing factors.

### 3. Phase 3 — AI Recovery Agent & Bounded Reasoning
- **Untrusted Reasoning Component**: The LLM is treated as an untrusted reasoning component, never a financial authority.
- **LLM Provider Abstraction**: Supports Google Gemini (`gemini-1.5-flash`), Groq (`llama3-70b-8192`), OpenAI (`gpt-4o-mini`), and a deterministic `MockLLMProvider` for offline testing.
- **Read-Only Tool Registry**: The agent only has access to read-only diagnostic tools (`get_payment_context`, `get_recovery_history`, `get_revenue_intelligence`, `get_merchant_context`, `get_recovery_policy`, `get_allowed_actions`). No database writes, SQL execution, or HTTP mutations.
- **Allowed-Action Registry**: Prohibited from inventing arbitrary actions. Must select from explicitly registered actions:
  - `RETRY_PAYMENT`
  - `REQUEST_ALTERNATE_PAYMENT_METHOD`
  - `SEND_PAYMENT_REMINDER`
  - `REQUEST_REAUTHENTICATION`
  - `WAIT_AND_RETRY`
  - `MANUAL_REVIEW`
  - `CLOSE_RECOVERY_CASE`
  - `ESCALATE`
- **Deterministic PolicyEngine**: The agent proposes; the `PolicyEngine` decides. The PolicyEngine enforces maximum retry limits, payment eligibility, recovery case state, parameter constraints, and approval requirements. The LLM can never override the PolicyEngine.
- **Prompt-Injection Defense**: All untrusted payment metadata and customer failure descriptions are sanitized and isolated within explicit XML boundary tags (`<UNTRUSTED_PAYMENT_DATA>`, `<UNTRUSTED_FAILURE_DATA>`).
- **Safe Decision Trace**: Persists structured observation, evidence, decision, reason, and confidence without exposing raw chain-of-thought or sensitive data.

---

## 🛠️ Environment Configuration

Copy `.env.example` to `.env` and configure your credentials:

```bash
# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here

# Database
DATABASE_URL=postgresql://recoverx:password@localhost:5432/recoverx

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
APP_ENV=development
LOG_LEVEL=INFO

# LLM Provider (Phase 3)
LLM_PROVIDER=gemini  # Options: gemini, groq, openai, mock
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LLM_API_KEY=
LLM_MODEL=gemini-1.5-flash
LLM_TIMEOUT_SECONDS=30
MAX_AGENT_STEPS=6
AGENT_VERSION=agent-v1
PROMPT_VERSION=recovery-prompt-v1
POLICY_VERSION=policy-v1

# Agent Policy Configuration
MAX_RETRY_ATTEMPTS=3
AGENT_CONFIDENCE_THRESHOLD=0.5
```

---

## ⚡ Quick Start with Docker

1. **Start all services**:
```bash
docker compose up --build -d
```

2. **Apply database migrations**:
```bash
docker compose exec backend alembic upgrade head
```

3. **Seed demo data & run Phase 2 intelligence analysis**:
```bash
docker compose exec backend python scripts/seed_demo_data.py
docker compose exec backend python scripts/seed_agent_demo.py
```

4. **Access the Application**:
- **React + TypeScript Production Dashboard**: `http://localhost:5173/` (or port `8080` in Docker)
- **Interactive OpenAPI Docs**: `http://localhost:8000/api/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

### 💻 Running Frontend Locally:
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Reference

### Phase 1: Payments, Webhooks & Recovery
- `POST /api/v1/webhooks/razorpay` — Ingest and verify Razorpay webhook (HMAC-SHA256, idempotent)
- `GET /api/v1/payments` — List normalized payments
- `GET /api/v1/payments/{payment_id}` — Get single payment detail
- `GET /api/v1/recovery/cases` — List recovery cases
- `GET /api/v1/recovery/cases/{case_id}` — Inspect single recovery case

### Phase 2: Revenue Intelligence
- `GET /api/v1/intelligence/overview` — Aggregated revenue metrics and risk distributions
- `GET /api/v1/intelligence/opportunities` — Paginated and filterable recovery opportunities
- `GET /api/v1/intelligence/opportunities/{result_id}` — Full telemetry & contributing factors for an opportunity
- `POST /api/v1/intelligence/analyze/{payment_id}` — Analyze single payment deterministically
- `POST /api/v1/intelligence/analyze` — Batch payment analysis

### Phase 3: AI Recovery Agent
- `POST /api/v1/agent/analyze/{opportunity_id}` — Launch AI agent investigation and plan synthesis
- `POST /api/v1/agent/preview/{opportunity_id}` — Dry run plan preview (no database persistence)
- `GET /api/v1/agent/runs/{run_id}` — Retrieve complete persisted agent run, plan, and validation result
- `GET /api/v1/agent/runs/{run_id}/trace` — Retrieve safe decision trace and tool execution audit

---

## 🧪 Comprehensive Test Suite

The test suite covers all unit, integration, evaluation, and security scenarios across all three phases:

```bash
# Run all tests
pytest backend/tests/ -v

# Run Phase 1 tests
pytest backend/tests/test_idempotency.py backend/tests/test_signature_verification.py backend/tests/test_state_transitions.py backend/tests/test_webhook_processing.py -v

# Run Phase 2 tests
pytest backend/tests/test_intelligence_components.py backend/tests/test_intelligence_integration.py backend/tests/test_scenario_validation.py -v

# Run Phase 3 tests
pytest backend/tests/test_agent_components.py backend/tests/test_agent_security.py backend/tests/test_agent_evaluation.py -v
```

### Scenario Evaluation Coverage:
1. **Scenario 1 (Temporary Failure)**: High-value temporary bank outage with 0 retries → Agent selects `WAIT_AND_RETRY` → PolicyEngine: `ALLOWED`.
2. **Scenario 2 (Insufficient Funds)**: Balance failure → Agent selects `REQUEST_ALTERNATE_PAYMENT_METHOD` → PolicyEngine: `ALLOWED`.
3. **Scenario 3 (Repeated Failures)**: 3 previous failed attempts → Retry limit reached → Agent/PolicyEngine routes to `MANUAL_REVIEW`.
4. **Scenario 4 (Low-Value Opportunity)**: ₹300 transaction → Low operational urgency → Conservative `SEND_PAYMENT_REMINDER`.
5. **Scenario 5 (Policy Block)**: Agent retry proposal when retry count exceeds max limit → PolicyEngine returns `BLOCKED` and safely falls back to `MANUAL_REVIEW`.

---

## 🔒 Security & Guardrails

| Guardrail | Implementation |
|---|---|
| **Financial Authority Isolation** | LLMs cannot modify database rows, execute retries, issue refunds, or trigger payments. |
| **Tool Read-Only Boundary** | Tools are strictly whitelisted and query-only (`ToolRegistry`). |
| **Deterministic Policy Authority** | The `PolicyEngine` deterministically validates every proposed plan. It cannot be bypassed by prompt manipulation. |
| **Prompt-Injection Sanitization** | Delimited boundaries and regex pattern stripping in `PlanValidator` and `build_recovery_prompt`. |
| **Cross-Merchant Tenant Isolation** | Queries and agent runs require merchant scope matching. |
| **Audit Trail** | All state transitions, webhook receipts, and agent tool executions are permanently recorded in `audit_events` and `agent_tool_calls`. |

---

## ⚠️ Phase 4 Action Execution Boundary

In accordance with enterprise safety standards:
- **Phase 3 strictly outputs a structured plan (`RecoveryPlan`).**
- **Action execution is completely disabled in Phase 3.**
- Phase 4 will introduce controlled webhook dispatchers, payment gateway retry execution, and customer communication channels with explicit human-in-the-loop approval gates.
