# WeFindBest AI Platform

Production-ready starter for an AI API SaaS platform:

- FastAPI backend on `http://localhost:8001`
- Next.js frontend on `http://localhost:3000`
- PostgreSQL via Docker Compose
- Alembic database migrations
- Email/password auth plus `x-api-key` authentication
- JWT access/refresh tokens, sessions, email verification, password reset
- Organizations, team members, roles, admin audit logs, API-key rotation
- Subscription billing with plans, quotas, rate limits, usage, invoices, payments, and coupons
- Usage logging for chat requests
- Swagger docs, health checks, metrics, tests, and CI
- Mock AI responses by default; no paid external API is required
- Unified AI Gateway for OpenAI, Anthropic, Google Gemini, Mistral, Cohere, Groq, Ollama, and OpenRouter
- Provider routing, retries, fallback models, streaming, token counting, cost tracking, and provider health checks
- Observability for API latency, request logs, error events, user activity, provider latency, token usage, cost, alerts, and system health

## Active Structure

```text
backend/                  FastAPI app, Alembic migrations, tests, Dockerfile
frontend/                 Next.js dashboard, Dockerfile
.github/workflows/ci.yml  Backend/frontend CI
docker-compose.yml        Local Postgres/API/frontend stack
README.md                 Setup and test guide
```

## Local Setup

Start PostgreSQL:

```powershell
docker compose up -d db
```

Install backend dependencies:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run migrations:

```powershell
alembic upgrade head
```

Run the backend:

```powershell
uvicorn app.main:app --reload --port 8001
```

Run the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Docker Setup

```powershell
docker compose up --build
```

The Docker stack runs:

- PostgreSQL on host port `5433`
- Backend on host port `8001`
- Frontend on host port `3000`

## Backend API

- `GET /health`
- `GET /health/db`
- `GET /metrics`
- `GET /observability/summary`
- `GET /observability/requests`
- `GET /observability/errors`
- `GET /observability/activity`
- `GET /observability/providers`
- `GET /observability/providers/latency`
- `GET /observability/alerts`
- `POST /observability/alerts`
- `POST /observability/alerts/{id}/ack`
- `POST /observability/alerts/{id}/resolve`
- `GET /observability/system-health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/verify-email`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `GET/POST /auth/api-keys`
- `POST /auth/api-keys/{id}/rotate`
- `GET/POST /auth/organizations`
- `POST /auth/organizations/{id}/members`
- `GET /auth/sessions`
- `GET /auth/login-history`
- `GET /auth/audit-logs`
- `GET /billing/plans`
- `GET /billing/subscription`
- `POST /billing/subscribe`
- `GET /billing/usage`
- `GET /billing/invoices`
- `GET /billing/payments`
- `GET/POST /billing/coupons`
- `POST /v1/chat`
- `POST /v1/chat/stream`
- `GET /v1/providers/health`

Protected chat routes require:

```text
x-api-key: your-api-key
```

Observability routes require a JWT bearer token from `POST /auth/register` or `POST /auth/login`.

## Swagger Test Flow

1. Open `http://127.0.0.1:8001/docs`.
2. Run `POST /auth/register` with:

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

3. Copy the returned `api_key`.
4. Click `Authorize`.
5. Paste the key into the `x-api-key` field.
6. Run `POST /v1/chat` with:

```json
{
  "input": "Hello from Swagger",
  "provider": "mock",
  "model": "mock",
  "temperature": 0.7,
  "fallback_models": ["mock"]
}
```

7. Run `POST /v1/chat/stream` with:

```json
{
  "input": "Stream a short answer",
  "provider": "mock",
  "model": "mock",
  "temperature": 0.7,
  "fallback_models": ["mock"]
}
```

## AI Gateway

The gateway supports these providers:

- `openai`
- `anthropic`
- `gemini`
- `mistral`
- `cohere`
- `groq`
- `ollama`
- `openrouter`
- `mock`

Configure provider credentials in `backend/.env`. Missing external provider credentials do not break local development; requests can fall back to `mock`.

```powershell
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
AI_GATEWAY_FALLBACK_MODELS=mock
AI_GATEWAY_MAX_RETRIES=2
```

Example fallback request:

```json
{
  "input": "Summarize this",
  "model": "gpt-4o-mini",
  "fallback_models": ["mock"]
}
```

## Billing

Seeded plans:

- Free
- Starter
- Pro
- Business
- Enterprise

Billing is local/mock by default. It tracks monthly request usage, monthly token usage, estimated cost, invoices, payment history, coupons, quotas, and per-minute rate limits.

## Observability

Every non-`/metrics` request is recorded with method, path, status, latency, request id, user context when available, and error metadata for server failures. Chat requests also record provider latency, token usage, estimated cost, and user activity.

Swagger flow:

1. Register or log in.
2. Copy `access_token`.
3. Click `Authorize` and paste `Bearer access_token` for protected observability routes.
4. Run `POST /v1/chat` with `x-api-key` to generate usage.
5. Check `GET /observability/summary`, `GET /observability/requests`, `GET /observability/providers`, and `GET /observability/system-health`.

Admin users can create and update alerts:

```json
{
  "severity": "warning",
  "title": "Latency threshold crossed",
  "message": "p95 latency is above target",
  "source": "api"
}
```

Subscribe with:

```json
{
  "plan_slug": "pro",
  "coupon_code": "SAVE20"
}
```

## Frontend Test Flow

1. Open `http://localhost:3000`.
2. Register a user.
3. Confirm you are redirected to `/dashboard`.
4. Confirm the API key input is populated.
5. Send a chat message and verify a mock response appears.

## Tests

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Database

Schema is managed by Alembic migrations in `backend/alembic`.

Create a new migration after model changes:

```powershell
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The `users` table includes `id`, `email`, `hashed_password`, `api_key`, and `created_at`.
Chat requests are logged in `usage_logs`.
