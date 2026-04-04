# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Phase 3 GCP deployment automation:**
  - `deploy-gcp.sh` – fully automated deployment script
  - `docs/DEPLOYMENT_GCP_STEPS.md` – detailed step-by-step guide
  - `load-tests/load_test.py` – load testing script (baseline 100 RPS)
  - `terraform.tfvars.example` – template for GCP variables
- **Documentation:**
  - `PROJECT_SUMMARY.md` – executive summary for stakeholders
  - `docs/PHASE2_REPORT.md` – testing & QA report with results
- **Development tools:**
  - Docker Compose configuration for local development
  - GitHub Actions CI/CD workflow (`.github/workflows/ci.yml`)
  - Alembic database migrations

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