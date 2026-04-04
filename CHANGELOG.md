# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Settings Management (Phase 2):**
  - `Skills` – catalog of agent capabilities (name, description, category)
  - `AI Models` – provider-agnostic model configuration (OpenAI, Anthropic, Ollama, etc.)
  - CRUD APIs for Skills (`/api/v1/settings/skills`) and AI Models (`/api/v1/settings/models`)
  - Model validation: agents must reference existing active models
  - Cost tracking fields: `cost_per_1k_input`, `cost_per_1k_output`
  - Flexible model config: custom base URLs, API keys, max tokens, context windows
- **Frontend (React + TypeScript + Vite):**
  - Complete SPA with authentication (login/register)
  - Dashboard with system overview
  - Agents page: create, edit, delete, list agents with dynamic model dropdown
  - Teams page: manage agent teams with member management
  - Runs page: list and monitor agent/team executions
  - API Keys page: manage machine authentication keys
  - Settings pages: Skills and AI Models management
  - React Query for data fetching with auto-refresh
  - Tailwind CSS for styling
  - Protected routes and JWT token management
- **Agent Updates:**
  - `PUT /api/v1/agents/{id}` endpoint for editing agents
  - Frontend edit modal pre-filled with existing data
  - Partial updates supported
- **Security Improvements:**
  - Distinct JWT error messages: "Token expired" vs "Invalid token"
  - Increased JWT expiry from 30min to 24h for developer convenience
  - Model validation prevents referencing inactive models (400 error)
- **Documentation:**
  - `CLAUDE.md` – developer onboarding guide for Claude Code
  - `docs/API_REFERENCE.md` – complete settings endpoints documentation
  - `frontend/FE_SETUP.md` – React development setup instructions
  - Updated `README.md` with new features and frontend info
- **Development Tools:**
  - Docker Compose configuration for full stack (backend + frontend)
  - Vite dev server with HMR
  - TypeScript strict mode
  - ESLint + Prettier configuration

### Changed
- `ACCESS_TOKEN_EXPIRE_MINUTES` default increased from 30 to 1440 (24 hours)
- Teams list query optimized with `selectinload` for eager loading of agents
- Update agent mutation now properly invalidates both single and list queries

### Fixed
- JWT decode now raises specific exceptions instead of blanket `None` return
- Agent edit modal now correctly loads all fields for editing
- Model dropdown populates from backend API instead of hardcoded list
- Inactive models are now filtered/indicated in the UI

### Security
- Backend validates model existence and active status before creating/updating agents
- API keys returned only on creation (not in GET responses)
- Tenant isolation enforced in all agent operations

### Changed
- Updated API endpoints to properly accept JSON request bodies using `Body(...)`
- Improved test isolation with unique tenant slugs in E2E tests
- Fixed Celery worker import structure (avoid circular imports)
- Updated requirements for compatibility (bcrypt/passlib versions)

### Fixed
- Docker deployment issues (asyncpg driver for Alembic)
- Router prefix duplication in main.py
- Missing imports (`Optional`, `Integer`) across models
- API key service import errors

### Security
- All secrets now loaded from environment/.env (not hardcoded)
- Bcrypt password hashing with proper work factor
- JWT token authentication with expiration
- SQL injection prevention via SQLAlchemy ORM
- Multi-tenancy isolation verified with tests

---

## [1.0.0] – 2026-04-04

### Added
- **Core Platform (Phase 1):**
  - Multi-tenant architecture with complete data isolation
  - FastAPI REST API with CRUD operations for agents, teams, runs, API keys
  - SQLAlchemy 2.0 async models: Tenant, User, Agent, Team, Run, APIKey
  - Celery background task processing for async agent execution
  - AGNO integration wrappers (TenantAwareAgent, TenantAwareTeam)
  - Structured JSON logging with structlog
  - Authentication: API keys (machine) + JWT (user) with OAuth2 password flow
  - Audit tracking: all runs logged with tokens, cost, duration, status
- **Infrastructure:**
  - Dockerfile for production containerization
  - Docker Compose for local development (Postgres, Redis, API, Celery, Flower)
  - Terraform modules for GCP (Cloud Run, Cloud SQL, Memorystore, Secret Manager)
  - Alembic migrations for database schema management
- **Testing:**
  - Unit tests (10 passing) for models, config, security
  - Integration tests (E2E) for full workflow verification
  - Load testing script achieving **1862 RPS** baseline (target 100)
- **Documentation (9 files):**
  - README.md – quick start guide
  - API_REFERENCE.md – complete endpoint documentation
  - ARCHITECTURE.md – system design and data flow
  - SECURITY.md – threat model and compliance
  - MULTI_TENANCY.md – isolation architecture
  - DEPLOYMENT.md – GCP deployment overview
  - DEPLOYMENT_GCP_STEPS.md – detailed walkthrough
  - EXAMPLES.md – usage examples (curl, Python SDK)
  - OPERATIONS.md – runbook, monitoring, incidents
- **Developer Tools:**
  - `scripts/create_tenant.py` – CLI tool to create tenants
  - `scripts/seed.py` – seed demo data for development
  - `pyproject.toml` – project metadata and tool configs (black, ruff, mypy, pytest)
  - `.github/workflows/ci.yml` – CI pipeline (test, lint, Docker build)

### Performance Benchmarks
- Health endpoint: **1862 RPS** (p95 latency 18ms)
- Agents list (JWT): **501 RPS** (p95 latency 70ms)
- Docker local: PostgreSQL F1-micro + Redis

### Security Posture
- ✅ SQL injection prevention (ORM)
- ✅ Bcrypt password hashing
- ✅ JWT signed with HS256
- ✅ Multi-tenancy isolation verified
- ✅ Structured audit logging
- ⚠️ Rate limiting pending (Phase 5)

---

## [0.1.0] – 2026-04-03

### Added
- Initial project structure and documentation (`docs/analisi.md`)
- Basic models and API skeleton
- Project plan and timeline (Italian)

---

*This changelog tracks all notable changes from project inception.*  
*Last updated: 2026-04-04*