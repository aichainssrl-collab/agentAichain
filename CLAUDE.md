# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended for local dev)

### Quick Start with Docker (Recommended)
```bash
# Start all services (Postgres, Redis, API, Celery worker, Flower)
docker-compose up -d

# View logs
docker-compose logs -f api

# Run database migrations (auto-run on API startup)
docker-compose exec api alembic upgrade head

# Seed demo data
docker-compose exec api python scripts/seed.py

# Create additional tenant
docker-compose exec api python scripts/create_tenant.py --name "Acme" --slug "acme" --email "admin@acme.com" --password "secure123"

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

# Seed demo data
python scripts/seed.py

# Run API (with auto-reload)
uvicorn agent_aichain.main:app --reload

# Run Celery worker (in separate terminal)
celery -A agent_aichain.workers.celery_app worker --loglevel=info

# Run Flower (monitoring UI)
celery -A agent_aichain.workers.celery_app flower --port=5555
```

## Common Commands

### Testing
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit -v

# Run integration tests (requires Postgres + Redis)
pytest tests/integration -v

# Run single test file
pytest tests/unit/test_models.py -v

# Run single test case
pytest tests/unit/test_models.py::test_tenant_creation -v

# With coverage
pytest --cov=agent_aichain --cov-report=html
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

## Architecture Overview

### High-Level Structure
```
agent_aichain/
├── main.py                    # FastAPI app, router registration, middleware
├── core/                      # Core infrastructure
│   ├── config.py             # Settings management (pydantic-settings)
│   ├── database.py           # Async engine, sessionmaker, get_db()
│   └── security.py           # Password hashing, JWT utilities
├── models/                    # SQLAlchemy ORM models
│   ├── base.py               # Declarative base, TimestampMixin
│   ├── tenant.py             # Tenant (multi-tenancy root)
│   ├── user.py               # User (belongs to tenant)
│   ├── api_key.py            # Machine auth keys
│   ├── agent.py              # AI agent definitions
│   ├── team.py               # Agent teams
│   ├── run.py                # Execution records
│   ├── skill.py              # Agent skills (NEW)
│   ├── aimodel.py            # AI model configs (NEW)
│   └── associations.py       # Many-to-many tables
├── api/                       # FastAPI routers & schemas
│   ├── auth.py               # Authentication endpoints
│   ├── agents.py             # Agent CRUD
│   ├── teams.py              # Team CRUD + agent management
│   ├── runs.py               # Run creation & polling
│   ├── api_keys.py           # API key management
│   ├── settings.py           # Skills & AI models (NEW)
│   └── schemas.py            # Pydantic request/response models
├── services/                  # Business logic layer
│   └── tenant_service.py     # Tenant operations
├── workers/                   # Async task execution
│   ├── celery_app.py         # Celery configuration
│   ├── tasks.py              # @celery.task definitions
│   └── agno_wrapper.py       # AGNO API client with context
└── utils/                     # Utilities (logging, etc.)
```

### Multi-Tenancy Pattern
- **Tenant Isolation**: All queries are scoped by `tenant_id`
- **Authentication**: Dual modes - API Key (machine) and JWT (user)
- **Row-Level Security**: Every query filters by `current_user.tenant_id`
- **Context Propagation**: `TenantAwareAgent` / `TenantAwareTeam` inject tenant ID into AGNO API calls

### Async Patterns
- Database: `AsyncSession` with `asyncpg`
- Endpoints: `async def` throughout
- Celery: Synchronous tasks (agent execution is blocking) but runs in separate workers
- External API calls: AGNO API is synchronous within Celery tasks

### Key Conventions
- **Models**: Inherit from `Base` and `TimestampMixin` (created_at, updated_at)
- **API**: All routes under `/api/v1/`, mounted via `app.include_router()`
- **Dependencies**: `get_db()` for DB session, `get_current_user()` for auth
- **Schemas**: Separate Pydantic models for Create/Update/Response
- **Testing**: `tests/unit` for isolated, `tests/integration` for full stack

### Settings Management (New)
The new `/settings` endpoints manage global configuration:
- **Skills**: Catalog of agent capabilities (search_kb, calculator, etc.)
- **AI Models**: Provider-agnostic model definitions with cost tracking
- Use JSON string `config` field for model-specific parameters
- API key storage: plaintext in DB (consider encryption for production)

## Important Files to Understand

- `agent_aichain/main.py` - App entry point, router setup, CORS
- `agent_aichain/core/database.py` - Connection pooling, session management
- `agent_aichain/api/auth.py` - Auth middleware, dependency injection
- `agent_aichain/workers/agno_wrapper.py` - Critical: How agents execute
- `alembic/versions/` - Migration history (each file is a checkpoint)

## Configuration

### Environment Variables (.env)
See `.env.example` for all available options. Key ones:
- `DATABASE_URL` - PostgreSQL async connection
- `REDIS_URL` - Redis connection
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` - Redis DB 1 & 2
- `SECRET_KEY` - JWT signing
- `AGNO_API_KEY` / `AGNO_BASE_URL` - External agent service
- `LOG_LEVEL` / `LOG_FORMAT` - Structured logging (json)

### Logging
Uses `structlog` for JSON logging. Configured in `main.py`. Logs to stdout.

## Deployment Notes
- Production uses GCP: Cloud Run (API), Cloud SQL (Postgres), Memorystore (Redis)
- Secrets managed via GCP Secret Manager
- Terraform infrastructure in `terraform/gcp/`
- See `docs/DEPLOYMENT.md` for full guide

## API Documentation
- Interactive Swagger: `/docs`
- ReDoc: `/redoc`
- Static reference: `docs/API_REFERENCE.md`

## Testing Strategy
- Unit tests mock database with `pytest-asyncio`
- Integration tests use actual Postgres/Redis via docker-compose
- E2E tests in `tests/integration/test_e2e.py` cover full agent execution flow

## Workflow for New Features
1. Create/update SQLAlchemy model in `models/`
2. Create Alembic migration: `alembic revision --autogenerate -m "msg"`
3. Create Pydantic schemas in `api/schemas.py`
4. Implement CRUD in router file (e.g., `api/agents.py`)
5. Add tests (unit for logic, integration for API)
6. Update `docs/API_REFERENCE.md`
7. Update `README.md` if user-facing changes

## Gotchas
- Always use `await` with database operations
- Never return plaintext API keys in GET responses (see `settings.py` - it currently does, should fix)
- Tenant isolation must be enforced in every query (use `current_user.tenant_id`)
- AGNO calls are blocking; keep them in Celery tasks only
- PostgreSQL connection pool size: default 10 (adjust for load)
