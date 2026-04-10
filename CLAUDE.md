# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other AI agents when working with code in this repository.

## Project Overview

AgentAichain is a **B2B multi-tenant AI agent orchestration platform** enabling enterprises to deploy, manage, and scale AI agents with complete data isolation and audit logging.

**Tech stack:** FastAPI 0.115+, SQLAlchemy 2.0 async, PostgreSQL 15, Redis 7, Celery, Neo4j 5, AGNO framework, React 18 + TypeScript (frontend), Docker Compose (local), Prometheus (metrics), GCP Terraform (production).

**Status:** Phase 1-2 complete. Phase 3 (Neo4j, AGNO Native, Security/Monitoring, Skill System) in advanced progress. Ready for GCP deployment.

---

## Development Environment

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended for local dev)

### Quick Start with Docker (Recommended)
```bash
# Start all services (Postgres, Redis, Neo4j, API, Celery worker, Flower)
docker-compose up -d

# View logs
docker-compose logs -f api

# Run database migrations (auto-run on API startup)
docker-compose exec api alembic upgrade head

# Seed demo skills (85+ skills across 20 categories)
docker-compose exec api python scripts/seed_skills.py

# Access API at http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Manual Setup (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev,gcp]"  # with dev and GCP extras

# Set environment variables (or copy .env.example to .env)
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/agent_aichain
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key
export AGNO_API_KEY=your-agno-key

# Initialize database
alembic upgrade head

# Seed skills catalog
python scripts/seed_skills.py

# Run API (with auto-reload)
uvicorn agent_aichain.main:app --reload

# Run Celery worker (in separate terminal)
celery -A agent_aichain.workers.celery_app worker --loglevel=info

# Run Flower (monitoring UI)
celery -A agent_aichain.workers.celery_app flower --port=5555
```

---

## Common Commands

### Testing
```bash
# Run all tests
python3 -m pytest

# Run unit tests only
python3 -m pytest tests/unit -v

# Run integration tests (requires Postgres + Redis)
python3 -m pytest tests/integration -v

# Run single test case
python3 -m pytest tests/unit/test_models.py::test_tenant_creation -v

# With coverage
python3 -m pytest --cov=agent_aichain --cov-report=html
```

### Code Quality
```bash
# Format code with Black
black agent_aichain/ tests/

# Lint with Ruff
ruff check agent_aichain/ tests/

# Type checking with mypy
mypy agent_aichain/

# Auto-fix lint issues
ruff check --fix agent_aichain/ tests/
```

### Database Migrations
```bash
# Create migration (after model changes)
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Show current revision
alembic current
```

### Docker Commands
```bash
# Rebuild and restart all
docker-compose down
docker-compose up -d --build

# Rebuild only API service
docker-compose build api
docker-compose up -d api

# Clean up volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Architecture Overview

### High-Level Structure
```
agent_aichain/
├── main.py                    # FastAPI app, middleware stack, lifespan, routers
├── core/                      # Infrastructure
│   ├── config.py             # Pydantic BaseSettings - all env vars
│   ├── database.py           # AsyncEngine, AsyncSession, tenant auto-filtering
│   ├── security.py           # bcrypt, JWT (HS256), token creation/verification
│   ├── tenant_context.py     # ContextVar for current tenant
│   └── neo4j_db.py           # Neo4j driver (sync + async)
├── models/                    # SQLAlchemy ORM models
│   ├── base.py               # DeclarativeBase + TimestampMixin
│   ├── tenant.py             # Tenant (plan, quotas, limits)
│   ├── user.py               # User (belongs to tenant)
│   ├── api_key.py            # Machine auth keys (hashed, expirable)
│   ├── agent.py              # AI agent (FK aimodel_id, tools, skills M:N)
│   ├── team.py               # Agent teams (coordinate/route/collaborate)
│   ├── run.py                # Execution records (status, tokens, cost)
│   ├── skill.py              # OpenClaw-style skill catalog (20 categories, agno mapping)
│   ├── aimodel.py            # Provider-agnostic AI model definitions
│   └── associations.py       # team_agents + agent_skills (M:N junction tables)
├── api/                       # FastAPI routers & schemas
│   ├── auth.py               # JWT + API Key auth, get_current_user()
│   ├── agents.py             # Agent CRUD + Neo4j similarity
│   ├── teams.py              # Team CRUD + agent management
│   ├── runs.py               # Run creation (Celery async) + SSE streaming
│   ├── api_keys.py           # API key create/revoke
│   ├── settings.py           # Skills + AI Models management
│   ├── graph.py              # Neo4j graph visualization
│   ├── schemas.py            # Pydantic request/response models
│   ├── versioning.py         # API versioning middleware
│   └── middleware/
│       └── tenant.py         # TenantContextMiddleware
├── services/                  # Business logic
│   ├── tenant_service.py     # Tenant creation/retrieval
│   ├── api_key_service.py    # Key generation, hashing, verification
│   └── graph_service.py      # Neo4j CRUD + similarity queries
├── workers/                   # Background execution
│   ├── celery_app.py         # Celery config (broker Redis, acks_late)
│   ├── tasks.py              # Celery tasks for agent/team runs
│   └── agno_wrapper.py       # TenantAwareAgent, TenantAwareTeam, dynamic skill→tool mapping
└── scripts/                    # Utility scripts
    └── seed_skills.py         # Seed 85+ skills across 20 OpenClaw-inspired categories
```

### Middleware Stack (order of registration)
1. **CORSMiddleware** - configured from `settings.cors_origins`, credentials enabled
2. **Security Headers** - `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `HSTS`, `CSP`
3. **TenantContextMiddleware** - extracts tenant from route path or JWT, sets context var
4. **Prometheus Metrics** - `REQUEST_COUNT` counter + `REQUEST_LATENCY` histogram (excludes `/metrics`)
5. **APIVersionMiddleware** - adds `API-Version` and `API-Supported-Versions` headers, deprecation/sunset policy

### Lifespan Events
- **Startup:** init DB → connect Neo4j → initialize graph schema
- **Shutdown:** close Neo4j connection

### Multi-Tenancy Pattern
- **Tenant Isolation**: Auto-applied via SQLAlchemy `with_loader_criteria` listener on every query
- **Disable filter** (dev only): `DISABLE_TENANT_FILTER=1`
- **Authentication**: Dual modes — API Key (`X-API-Key`) or JWT Bearer
- **Context propagation**: `current_tenant_id` ContextVar set by auth/middleware, read by DB listener
- **ContextVar code**: `agent_aichain/core/tenant_context.py`
- **DB listener**: `agent_aichain/core/database.py` — `add_listener` on query events

### Async Patterns
- Database: `AsyncSession` with `asyncpg`, `expire_on_commit=False`
- Endpoints: `async def` throughout
- Celery tasks: synchronous (blocking) but run in separate worker processes
- Celery tasks create **isolated NullPool engines** to avoid event loop conflicts
- External API calls in Celery tasks (AGNO execution is blocking)

### Auth Flow
1. Client sends `Authorization: Bearer <jwt>` or `X-API-Key: <key>`
2. `get_current_user()` in `auth.py` verifies and loads User
3. `context.set_current_tenant_id(user.tenant_id)`
4. All subsequent queries auto-filter by that tenant via DB listener

---

## Database Models

### Tenant (`models/tenant.py`)
- `name` (unique), `slug` (unique), `plan` (free/pro/enterprise)
- Quotas: `max_agents` (10), `max_teams` (5), `max_runs_per_month` (10000)

### User (`models/user.py`)
- `email`, `hashed_password`, `tenant_id` (FK), `is_active`, `is_superuser`, `last_login`

### APIKey (`models/api_key.py`)
- `key` (raw), `hashed_key` (bcrypt), `owner_id` (FK User), `expires_at`, `usage_count`
- Methods: `is_expired()`

### Agent (`models/agent.py`)
- `name`, `role`, `aimodel_id` (FK AIModel), `tools` (JSON list), `instructions` (text), `config` (JSON)
- **M:N with Skill** via `agent_skills` table (`agent.skills` relationship, `selectin` lazy)

### Team (`models/team.py`)
- `name`, `mode` (coordinate/route/collaborate), `max_iterations`, `config` (JSON)
- M:N with `agents` via `team_agents` table

### Run (`models/run.py`)
- `task` (text), `input` (JSON), `output` (JSON), `status` (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED)
- `tokens_used`, `cost`, `duration_ms`, `celery_task_id`, `agent_id` (nullable), `team_id` (nullable)

### AIModel (`models/aimodel.py`)
- `name`, `provider` (openai/anthropic/google/ollama/openrouter/custom), `base_url`, `api_key`
- `max_tokens`, `max_context`, `cost_per_1k_input`, `cost_per_1k_output`
- `config` (JSON text for custom params), `tenant_id` (FK)
- Unique constraint on `(name, tenant_id)`

### Skill (`models/skill.py`)
- `name` (unique), `description`, `category` (20 OpenClaw-inspired categories), `agno_tool_class` (maps to Agno Tool class like `DuckDuckGoTools`), `agno_tool_params` (JSON params for tool instantiation), `is_active`
- **Categories**: productivity, development, communication, research, ai_models, marketing, sales, finance, cloud, devops, security, data, content, social_media, media_generation, integration, automation, iot, custom
- **M:N with Agent** via `agent_skills` table

### Associations (`models/associations.py`)
- `team_agents` — M:N Team ↔ Agent
- `agent_skills` — M:N Agent ↔ Skill

---

## API Endpoints (all under `/api/v1/`)

| Router | Endpoints | Auth | Notes |
|--------|-----------|------|-------|
| `auth.py` | POST `/auth/token`, POST `/auth/register-tenant` | None | Returns JWT or creates tenant+admin |
| `agents.py` | GET/POST `/agents`, GET/PUT/DELETE `/agents/{id}`, GET `/agents/{id}/similar` | JWT/Key | Auto-syncs to Neo4j on create/update |
| `teams.py` | GET/POST `/teams`, GET/DELETE `/teams/{id}`, POST/DELETE `/teams/{id}/agents/{aid}` | JWT/Key | Eager-loads agents via `selectinload` |
| `runs.py` | POST `/runs/agent/{id}`, POST `/runs/team/{id}`, POST `/runs/agent/{id}/stream`, GET `/runs/{id}`, GET `/runs` | JWT/Key | Celery async + SSE streaming |
| `api_keys.py` | GET/POST `/api-keys`, DELETE `/api-keys/{id}` | JWT only | Raw key shown only on create |
| `settings.py` | GET/POST/PUT/DELETE `/settings/skills/*`, GET/POST/PUT/DELETE `/settings/models/*` | JWT only | Skills and AI models CRUD |
| `graph.py` | GET `/graph/tenant` | JWT/Key | Full Neo4j graph `{nodes, links}` |

Non-versioned: `GET /health`, `GET /`

### Prometheus Metrics
- `GET /metrics` — Prometheus-format metrics (`http_requests_total`, `http_request_duration_seconds`)
- `/metrics` endpoint excluded from its own tracking

---

## Workers & AGNO Wrapper

### Celery (`workers/celery_app.py`)
- Broker: Redis DB 1, Backend: Redis DB 2
- `task_acks_late = True`, `worker_prefetch_multiplier = 1`
- Max tasks per worker: 1000

### Tasks (`workers/tasks.py`)
- `run_agent_task(run_id)` → `execute_agent_run()` (async)
- `run_team_task(run_id)` → `execute_team_run()` (async)
- Each task creates isolated AsyncEngine (NullPool) to avoid event loop conflicts

### AGNO Wrapper (`workers/agno_wrapper.py`)

**TenantAwareAgent**: wraps an Agent for agno execution
- Maps AIModel `provider` → agno model class (OpenAIChat, Anthropic, OpenRouter, Ollama; fallback: OpenAIChat)
- Maps agent's **skills** → agno Tool instances via `skill.agno_tool_class` (dynamic, not hardcoded)
- Falls back to string-based tool names in `agent.tools` for backward compatibility
- Execution: `_run_with_agno_lib()` (runs in thread pool via `run_in_executor`)
- Streaming: `arun_stream()` yields SSE-format chunks
- Returns `{output, tokens_used, cost}`

**TenantAwareTeam**: wraps a Team for coordinated agno execution
- Creates agno Agent per team member, wraps in agno Team
- Runs via thread pool
- Returns aggregated response

**Skill → Tool mapping**:
- Each Skill has `agno_tool_class` (e.g. `"DuckDuckGoTools"`, `"CalculatorTools"`)
- Wrapper dynamically `importlib.imports` the class from `agno.tools.*` and instantiates it
- Supports `agno_tool_params` as JSON for tool constructor arguments
- Unknown `agno_tool_class` logs a warning and is skipped
- Backward compatible: `agent.tools` (string list) still works for legacy agents

**Streaming endpoint** (`runs.py`): `POST /runs/agent/{agent_id}/stream`
- Uses `StreamingResponse` with `media_type="text/event-stream"`
- Yields `{content, done, run_id}` events via `arun_stream()`

---

## AGNO Providers Supported

| Provider | Model Class | Notes |
|----------|-------------|-------|
| `openai` | OpenAIChat | Default fallback |
| `anthropic` | Anthropic | Claude models |
| `openrouter` | OpenRouter | Multi-model aggregator |
| `ollama` | Ollama | Local models |
| `google` | GoogleGenAI | Gemini models |
| `custom` | OpenAIChat | Compatible API URL |

---

## Neo4j Integration

- **Driver**: `agent_aichain/core/neo4j_db.py` — `Neo4jConnection` sync + async
- **Graph service**: `agent_aichain/services/graph_service.py`
  - `initialize_schema()` → constraints and indexes on first run
  - `sync_tenant()`, `sync_agent()`, `sync_team()` → MERGE nodes
  - `link_agent_to_tool()`, `link_agent_to_team()` → create relationships
  - `get_similar_agents(agent_id, tenant_id)` → Cypher MATCH on shared tools
  - `get_tenant_graph(tenant_id)` → `{nodes, links}` for visualization
- **Auto-sync**: agents and teams sync to Neo4j on create/update (background task)
- **Graceful degradation**: Neo4j is optional — app starts if connection fails

---

## Services

| Service | File | Purpose |
|---------|------|---------|
| TenantService | `services/tenant_service.py` | Create tenant + admin user, retrieve by slug |
| APIKeyService | `services/api_key_service.py` | Generate raw+hashed keys, verify and update usage stats |
| GraphService | `services/graph_service.py` | All Neo4j operations (nodes, relationships, queries) |

---

## Configuration

### Environment Variables (.env)
See `.env.example`. Key variables:
- `DATABASE_URL` — PostgreSQL async connection
- `REDIS_URL` — Redis connection (main app)
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Redis DB 1 & 2
- `SECRET_KEY` — JWT signing key
- `AGNO_API_KEY` / `AGNO_BASE_URL` — AGNO service credentials
- `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` — Neo4j connection
- `LOG_LEVEL` / `LOG_FORMAT` — structured logging (json)
- `DISABLE_TENANT_FILTER` — set `1` to disable auto-tenant scoping (dev only)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT expiry (default: 30 min)

### Docker Compose Services
| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `postgres` | postgres:15-alpine | 5432 | Relational database |
| `redis` | redis:7-alpine | 6379 | Cache, broker, result backend |
| `neo4j` | neo4j:5 | 7474/7687 | Graph database |
| `api` | python:3.11-slim | 8000 | FastAPI (uvicorn --reload) |
| `celery-worker` | python:3.11-slim | - | Background task execution |
| `flower` | python:3.11-slim | 5555 | Celery monitoring UI |

### Frontend (`frontend/`)
- React 18 + TypeScript, Vite, Tailwind CSS
- React Query for server state, React Router v6
- See `frontend/FE_SETUP.md` for setup

---

## Alembic Migrations

| Migration | Description |
|-----------|-------------|
| `e9f8fa1bba37` | Create skills and ai_models tables |
| `531e1589cb88` | Add base_url, api_key columns to ai_models |
| `02322111f175` | Add aimsodel_id FK on agents (replaces model string) |
| `bb498020c058` | Add tenant_id FK on ai_models (tenant-scoped models) |

**Pending**: `agent_skills` table + `agno_tool_class`/`agno_tool_params` on skills

---

## Testing Strategy

- **Unit tests** (`tests/unit/`): isolated logic tests
  - `test_security.py` — password hashing, JWT, token expiry
  - `test_config.py` — settings loading
  - `test_models.py` — model creation and relationships
  - `test_agno_wrapper.py` — AGNO integration
  - `test_versioning.py` — API versioning middleware (6 tests)
- **Integration tests** (`tests/integration/`): full stack with Postgres/Redis
  - `test_tenancy.py` — tenant isolation
  - `test_api_multi_tenant.py` — multi-tenant API behavior
  - `test_e2e.py` — end-to-end agent execution
  - `test_teams.py` — team CRUD + agent management
- Test config in `pyproject.toml`: pytest-cov + pytest-asyncio

---

## Deployment Notes

### Local (Docker Compose)
All services via `docker-compose up -d`: Postgres, Redis, Neo4j, API, Celery, Flower.

### GCP (Terraform)
Infrastructure in `terraform/gcp/`:
- VPC network (10.0.0.0/24)
- Cloud SQL PostgreSQL (db-f1-micro, POSTGRES_15)
- Cloud Memorystore Redis (1GB, REDIS_7)
- Secret Manager for credentials
- APIs enabled: CloudRun, CloudSQL, Redis, SecretManager, Monitoring, Logging
- See `docs/DEPLOYMENT.md` for full guide

### Production considerations
- API key storage: plaintext in DB (encrypt for production)
- JWT expiry: 30 min (increase for developer convenience if needed)
- Dockerfile: currently single-stage (optimize with multi-stage for production)
- Neo4j: optional — app starts gracefully without it
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options active
- Prometheus metrics: exposed at `/metrics` for Grafana/Cloud Monitoring

---

## API Documentation
- Interactive Swagger: `/docs` and `/redoc`
- Static reference: `docs/API_REFERENCE.md`

---

## Workflow for New Features

1. Create/update SQLAlchemy model in `models/`
2. Create Alembic migration: `alembic revision --autogenerate -m "msg"`
3. Create Pydantic schemas in `api/schemas.py`
4. Implement CRUD in router file (e.g., `api/agents.py`)
5. Add tests (unit for logic, integration for API)
6. Update documentation if user-facing changes

---

## Gotchas

- **SECURITY WARNING: NEVER hardcode API keys** (OpenAI, OpenRouter, AGNO, GCP, etc.) in any file, script, test, or commit. Always use environment variables or dummy strings (`sk-dummy-key`) for testing.
- **Always use `await`** with database operations
- **Never return plaintext API keys** in GET responses (`settings.py` currently does — should fix)
- **Tenant isolation enforced automatically** — DB listener injects filter for every query
- **AGNO calls are blocking** — keep them in Celery tasks only
- **PostgreSQL connection pool** — default 10 (adjust for load)
- **Celery tasks need isolated engines** — they use NullPool to avoid event loop conflicts
- **`DISABLE_TENANT_FILTER=1`** — dev-only, DANGEROUS in production
- **StreamingResponse session** — DB session may close before streaming completes (guarded with try/except in `runs.py`)
- **`agno` module not installed in dev** by default — `test_agno_wrapper.py` fails without it (`pip install agno`)
- **Middleware order matters** — CORS → Security Headers → TenantContext → Prometheus → Versioning
