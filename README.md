# RecoverX — Phase 1: Financial Event Foundation

## Overview

RecoverX is an autonomous AI revenue-recovery platform. Phase 1 establishes the financial event foundation that all later phases depend on, implementing a production-quality backend capable of receiving Razorpay webhook events, verifying authenticity, handling duplicate delivery safely, and maintaining normalized payment state.

## Phase 1 Architecture

```
Razorpay Test Mode
        ↓
Webhook Event
        ↓
Signature Verification (HMAC-SHA256)
        ↓
Idempotency Check (x-razorpay-event-id)
        ↓
Raw Event Persistence (WebhookEvent)
        ↓
Async Queue (Redis)
        ↓
Background Processing
        ↓
Payment Normalization (Payment, PaymentAttempt)
        ↓
Recovery Case Creation (RecoveryCase)
        ↓
Audit Trail (AuditEvent)
        ↓
API Inspection
```

### Key Architectural Decisions

**Modular Monolith**: We chose a modular monolith architecture using FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, and Docker. This provides transactional consistency and development speed without introducing premature distributed-system complexity.

**PostgreSQL for Financial Domain**: Our core relationships are strongly relational (Merchant → Customer → Payment → PaymentAttempt → RecoveryCase). PostgreSQL provides transactions, unique constraints, foreign keys, and strong consistency.

**Raw Event + Normalized State**: We preserve the immutable Razorpay event in WebhookEvent for auditability and separately maintain normalized domain state (Payment, PaymentAttempt, RecoveryCase) for efficient queries and business logic.

**Webhook Signature Verification**: We verify Razorpay signatures using HMAC-SHA256 against the raw HTTP request body (not re-serialized JSON) with constant-time comparison to prevent timing attacks.

**Idempotent Event Processing**: Using `x-razorpay-event-id` with a unique constraint ensures duplicate webhook delivery creates no duplicate domain objects.

**Out-of-Order Event Handling**: Our state transition logic supports valid later events (e.g., FAILED → CAPTURED) to handle webhooks that may arrive out of order.

## Local Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running locally without Docker)

### Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/joshi-chinmay-016/RecoverX.git
cd RecoverX
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials:
```bash
# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here

# Database (already configured in docker-compose.yml)
DATABASE_URL=postgresql://recoverx:123cj123CJ*@localhost:5432/recoverx

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

4. Start the development environment:
```bash
docker compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Webhook worker

5. Run database migrations:
```bash
docker compose exec backend alembic upgrade head
```

6. (Optional) Seed development data:
```bash
docker compose exec backend python scripts/seed_data.py
```

### Local Development without Docker

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up PostgreSQL and Redis locally

3. Configure environment variables in `.env`

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Start the worker (in another terminal):
```bash
python -m app.workers.webhook_worker
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RAZORPAY_KEY_ID` | Razorpay API key ID | Yes |
| `RAZORPAY_KEY_SECRET` | Razorpay API key secret | Yes |
| `RAZORPAY_WEBHOOK_SECRET` | Razorpay webhook secret for signature verification | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `APP_ENV` | Application environment (development/production) | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No |

## Database Migrations

We use Alembic for database schema management.

### Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migrations:
```bash
alembic downgrade -1
```

### View migration history:
```bash
alembic history
```

## Database Schema

### Core Entities

**Merchant**: Represents a business entity receiving payments
- `id` (UUID, PK)
- `name` (String)
- `external_id` (String, unique)
- `currency` (String, default: INR)

**Customer**: Represents a customer making payments
- `id` (UUID, PK)
- `external_customer_id` (String, unique)
- `email` (String, optional)
- `phone` (String, optional)

**Payment**: Represents a logical payment
- `id` (UUID, PK)
- `razorpay_payment_id` (String, unique)
- `razorpay_order_id` (String, optional)
- `merchant_id` (UUID, FK)
- `customer_id` (UUID, FK, optional)
- `amount_minor` (Integer) - stored in paise (minor units)
- `currency` (String)
- `status` (Enum: CREATED, AUTHORIZED, CAPTURED, FAILED)
- `method` (String, optional)
- `failure_code` (String, optional)
- `failure_description` (String, optional)

**PaymentAttempt**: Represents individual payment attempts
- `id` (UUID, PK)
- `payment_id` (UUID, FK)
- `attempt_number` (Integer)
- `status` (Enum)
- `failure_code` (String, optional)
- `failure_description` (String, optional)
- `method` (String, optional)
- `started_at` (DateTime)
- `completed_at` (DateTime, optional)
- Unique constraint: (payment_id, attempt_number)

**WebhookEvent**: Immutable provider event
- `id` (UUID, PK)
- `provider_event_id` (String, unique)
- `provider` (String, default: razorpay)
- `event_type` (String)
- `payload` (JSONB)
- `signature_verified` (Boolean)
- `processing_status` (Enum: RECEIVED, PROCESSING, PROCESSED, FAILED, IGNORED)
- `received_at` (DateTime)
- `processed_at` (DateTime, optional)
- `error_message` (Text, optional)

**RecoveryCase**: Represents a recovery case for failed payments
- `id` (UUID, PK)
- `payment_id` (UUID, FK)
- `status` (Enum: OPEN, RESOLVED, CLOSED)
- `amount_at_risk_minor` (Integer)

**AuditEvent**: Audit trail for all important state changes
- `id` (UUID, PK)
- `entity_type` (String)
- `entity_id` (UUID)
- `event_type` (Enum: WEBHOOK_RECEIVED, PAYMENT_CREATED, PAYMENT_STATUS_CHANGED, RECOVERY_CASE_CREATED, etc.)
- `actor_type` (Enum: SYSTEM, WEBHOOK, AGENT, USER)
- `audit_metadata` (JSONB)

## Webhook Setup

### Razorpay Test Mode Configuration

1. Log into Razorpay Dashboard (Test Mode)
2. Navigate to Settings → Webhooks
3. Add a new webhook:
   - **Webhook URL**: Your publicly accessible URL (e.g., from ngrok: `https://your-url.ngrok.io/api/v1/webhooks/razorpay`)
   - **Secret**: Copy the webhook secret to your `.env` file as `RAZORPAY_WEBHOOK_SECRET`
4. Select events to subscribe:
   - `payment.failed`
   - `payment.authorized`
   - `payment.captured`

### Local Webhook Testing

For local development, use a tunnel service like ngrok:

1. Install ngrok:
```bash
# On macOS
brew install ngrok

# On Windows
# Download from https://ngrok.com/download
```

2. Start ngrok:
```bash
ngrok http 8000
```

3. Use the ngrok HTTPS URL in Razorpay webhook configuration

4. Test webhooks using Razorpay Dashboard test events or API

### Webhook Security

**Signature Verification**: All webhooks are verified using HMAC-SHA256 with the raw request body (not re-serialized JSON) to prevent tampering.

**Idempotency**: We use the `x-razorpay-event-id` header with a unique constraint to ensure duplicate webhook delivery creates no duplicate domain objects.

**Raw Body Preservation**: We read the raw bytes before JSON parsing to ensure signature validation works correctly.

## API Endpoints

### Health Check
```http
GET /api/v1/health
```
Response:
```json
{
  "status": "ok"
}
```

### Razorpay Webhook
```http
POST /api/v1/webhooks/razorpay
```
Headers:
- `x-razorpay-signature`: HMAC signature
- `x-razorpay-event-id`: Unique event ID

Response:
```json
{
  "status": "received",
  "message": "Webhook received and queued"
}
```

### List Webhook Events
```http
GET /api/v1/webhooks/events
```
Query Parameters:
- `event_type` (optional): Filter by event type
- `processing_status` (optional): Filter by processing status
- `from` (optional): Filter from date
- `to` (optional): Filter to date
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Page size

Response:
```json
{
  "events": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Get Webhook Event
```http
GET /api/v1/webhooks/events/{event_id}
```

### List Payments
```http
GET /api/v1/payments
```
Query Parameters:
- `status` (optional): Filter by payment status
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Page size

Response:
```json
{
  "payments": [...],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

### Get Payment
```http
GET /api/v1/payments/{payment_id}
```
Response includes payment, attempts, and recovery case:
```json
{
  "id": "...",
  "razorpay_payment_id": "pay_123",
  "status": "FAILED",
  "amount_minor": 1000,
  "attempts": [...],
  "recovery_case": {...}
}
```

### List Recovery Cases
```http
GET /api/v1/recovery/cases
```
Query Parameters:
- `status` (optional): Filter by recovery case status (OPEN, RESOLVED, CLOSED)
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Page size

Response:
```json
{
  "cases": [...],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

### Get Recovery Case
```http
GET /api/v1/recovery/cases/{case_id}
```

## Testing

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test File
```bash
pytest tests/test_signature_verification.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Test Categories

**Signature Verification Tests** (`tests/test_signature_verification.py`):
- Valid signature acceptance
- Invalid signature rejection
- Modified payload rejection

**Idempotency Tests** (`tests/test_idempotency.py`):
- Duplicate event detection
- No duplicate for new events
- Duplicate events not processed again

**State Transition Tests** (`tests/test_state_transitions.py`):
- Valid transitions (CREATED → AUTHORIZED, AUTHORIZED → CAPTURED, etc.)
- Out-of-order support (FAILED → CAPTURED)
- Invalid transitions (CAPTURED → any)

**Webhook Processing Tests** (`tests/test_webhook_processing.py`):
- payment.failed creates recovery case
- Unknown event types ignored
- Invalid signature rejected

## Event Flow

### payment.failed
```
WebhookEvent → Find/create Payment → Create PaymentAttempt → 
Update Payment status = FAILED → Create RecoveryCase → AuditEvent
```

### payment.authorized
```
WebhookEvent → Find Payment → Update status = AUTHORIZED → AuditEvent
```

### payment.captured
```
WebhookEvent → Find Payment → Update status = CAPTURED → 
Resolve any active recovery case → AuditEvent
```

## Project Structure

```
recoverx/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── core/
│   │   │   ├── config.py           # Configuration management
│   │   │   ├── security.py         # Security utilities
│   │   │   └── logging.py          # Logging configuration
│   │   ├── db/
│   │   │   ├── base.py             # Base model and enums
│   │   │   ├── session.py          # Database session management
│   │   │   └── models/             # SQLAlchemy models
│   │   ├── modules/
│   │   │   ├── webhooks/           # Webhook handling
│   │   │   ├── payments/           # Payment management
│   │   │   └── recovery/           # Recovery case management
│   │   ├── workers/
│   │   │   └── webhook_worker.py  # Background webhook processor
│   │   └── utils/
│   │       └── audit.py            # Audit service
│   ├── alembic/                    # Database migrations
│   ├── tests/
│   │   ├── fixtures/               # Test data fixtures
│   │   ├── test_signature_verification.py
│   │   ├── test_idempotency.py
│   │   ├── test_state_transitions.py
│   │   └── test_webhook_processing.py
│   ├── scripts/
│   │   └── seed_data.py            # Development data seeding
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── docker-compose.yml
├── .env.example
└── README.md
```

## Observability

The system tracks the following metrics for future dashboard integration:
- `webhooks_received`
- `webhooks_processed`
- `webhooks_failed`
- `duplicate_webhooks`
- `payment_failures`
- `payment_captures`
- `recovery_cases_created`

## Known Limitations

1. **Single Merchant**: Phase 1 uses a single development merchant, but the schema supports multiple merchants.
2. **Basic Recovery Logic**: Recovery cases are created for all failed payments without sophisticated recoverability scoring (Phase 2).
3. **No AI Components**: Phase 1 focuses on the financial foundation only; AI agent, ML models, and recovery strategies are not implemented.
4. **Local Testing**: Webhook testing requires tunnel services like ngrok for local development.

## Next Steps for Phase 2

Phase 2 will build on this foundation to add:
- Revenue Intelligence with recoverability scoring
- Historical recovery behavior analysis
- Payment failure pattern recognition
- Customer risk profiling
- Advanced recovery case prioritization
