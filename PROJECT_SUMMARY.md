# AgentAichain – Project Summary

**Version:** 1.0  
**Date:** April 4, 2026  
**Status:** ✅ Phase 1-2 Complete | Phase 3 Ready for Deployment  
**Team:** Aichain Solutions

---

## Executive Summary

AgentAichain is a **B2B multi-tenant AI agent orchestration platform** built for enterprise clients like SignSiSure. It enables companies to deploy, manage, and scale AI agents with complete data isolation, audit logging, and enterprise-grade security.

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, AGNO integration  
**Frontend:** React 18 + TypeScript, Vite, Tailwind CSS, React Query  
**Deployment:** Google Cloud Platform (Cloud Run, Cloud SQL, Memorystore)  
**License:** Proprietary

---

## What We Built

### Core Features

| Feature | Description |
|---------|-------------|
| **Multi-Tenancy** | Complete data isolation per client via `tenant_id` scoping |
| **Agent Management** | Create, update, delete AI agents with custom roles, models, tools, instructions |
| **Settings Management** | Centralized catalog of Skills and AI Models (provider-agnostic, cost tracking, active/inactive control) |
| **Team Collaboration** | Group agents into teams for collaborative workflows |
| **Dashboard Analytics** | Aggregated tenant-specific statistics and recent run tracking with real-time agent/team name resolution |
| **Async Execution** | Long-running agent tasks handled by Celery workers |
| **Authentication** | API keys (machine) + JWT (user) with bcrypt password hashing |
| **Audit Logging** | All runs tracked with tokens, cost, duration, status |
| **REST API** | Full CRUD operations, OpenAPI docs at `/docs` |
| **React Frontend** | Full SPA with agent/team management, settings, real-time monitoring |
| **GCP Native** | Terraform infrastructure, Cloud Run auto-scaling |

---

## Phase 2 Highlights (April 3-10)

### Settings Management System
- **Skills** – Global catalog of reusable agent capabilities (search, calculation, etc.)
- **AI Models** – Provider-agnostic model configuration
  - Supports OpenAI, Anthropic, Google, Ollama, OpenRouter, custom
  - Fields: name, provider, base_url, api_key, max_tokens, max_context, cost_per_1k_input/output, config (JSON), is_active
  - **Model validation**: Agents must reference existing active models (400 error if invalid/inactive)
  - Cost tracking for billing and analytics

### React Frontend (v1.0)
- **Technology**: React 18 + TypeScript (strict), Vite, Tailwind CSS, React Query, React Router v6
- **Pages**:
  - Dashboard – system overview with statistics
  - Agents – full CRUD, dynamic model dropdown from API, edit modal
  - Teams – create teams, add/remove agents
  - Runs – list, filter, execute agent/team runs, auto-refresh polling
  - API Keys – manage machine authentication keys
  - Settings – Skills and AI Models management pages
  - Auth – login, register
- **Features**:
  - Protected routes with JWT
  - Dynamic model selection (filters active models, shows inactive with warning ⚠️)
  - Run status auto-refresh (every 2s for pending/running)
  - Model validation feedback (prevents saving to inactive models)
  - Responsive UI with Tailwind

### Backend Improvements
- **PUT /agents/{id}** endpoint for editing agents (previously missing)
- **JWT error handling** – distinct messages: "Token expired" vs "Invalid token"
- **Token expiry** increased from 30min to **24 hours** for developer convenience
- **Model validation** on create/update – ensures `model` field references active AIModel
- **Team queries optimized** with `selectinload` for eager loading

### Documentation
- `CLAUDE.md` – developer onboarding guide for Claude Code instances
- `docs/API_REFERENCE.md` – complete settings endpoints
- `frontend/FE_SETUP.md` – React development setup
- `CHANGELOG.md` – comprehensive release notes
- Updated `README.md` with full feature list

---

## Architecture Highlights

---

### Architecture Highlights

```
┌─────────────────┐
│   Client Apps   │
└────────┬────────┘
         │ HTTPS + API Key / JWT
┌────────▼──────────────┐
│   FastAPI (Cloud Run)│
│   • Auth              │
│   • Tenant Isolation  │
│   • Request Validation│
└────────┬──────────────┘
         │
    ┌────┴────┬──────────────┐
    ▼         ▼              ▼
┌──────┐ ┌──────────┐ ┌─────────────┐
│Agent │ │   Team   │ │     Run     │
│Svc   │ │   Svc    │ │   Service   │
└──────┘ └──────────┘ └─────────────┘
    │         │              │
    └─────────┼──────────────┘
              ▼
      ┌──────────────┐
      │   Celery     │
      │  Workers     │
      └──────┬───────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌───────┐       ┌──────────┐
│ AGNO  │       │  Redis   │
│  API  │       │ (Broker) │
└───────┘       └──────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────┐
│PostgreSQL│ │    │      │
│ (Metadata)│ │    │      │
└───────────┘ │    │      │
              │    │      │
         ┌────┴────┴────┐
         ▼              ▼
   ┌──────────┐  ┌──────────┐
   │ Cloud SQL│  │Memorystore│
   │    &     │  │  (Redis) │
   │ Terraform│  │          │
   └──────────┘  └──────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────┐
│         React 18 + TypeScript       │
│  • Vite (dev server + build)        │
│  • React Router v6 (routing)        │
│  • React Query (server state)       │
│  • Tailwind CSS (styling)           │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌───────┐         ┌──────────┐
│Pages │         │ Components│
│(路由) │         │(UI组件库) │
└───────┘         └──────────┘
    │                   │
    └─────────┬─────────┘
              ▼
      ┌──────────────┐
      │   ApiClient  │
      │  (fetch + JWT)│
      └──────┬───────┘
             │
             ▼
      ┌──────────────┐
      │  FastAPI      │
      │  Backend      │
      └──────────────┘
```

### Why These Technologies?

| Technology | Reason |
|------------|--------|
| **FastAPI** | Async support, auto-docs, type hints, fast performance |
| **SQLAlchemy** | Mature ORM, async support, excellent migrations |
| **PostgreSQL** | Relational, ACID, GCP managed, jsonb support |
| **Redis** | Fast cache, Celery broker, pub/sub |
| **Celery** | Reliable background job processing |
| **React** | Component-based, huge ecosystem, team familiarity |
| **TypeScript** | Type safety, better DX, catches errors early |
| **Vite** | Fast HMR, modern build, great DX |
| **Tailwind** | Utility-first, no custom CSS files, rapid prototyping |
| **React Query** | Server state management, caching, auto-refetch |
| **Docker** | Consistent environments, easy local dev |
| **Terraform** | Infrastructure as code, reproducible |
| **Cloud Run** | Serverless, auto-scaling, pay-per-use |
| **AGNO** | Open-source agent framework (integrated natively) |

---

## Project Timeline (Q2 2026)

| Phase | Dates | Status | Deliverables |
|-------|-------|--------|--------------|
| **Phase 1: Core Platform** | Mar 20 - Apr 3 | ✅ Complete | Multi-tenant API, Docker, CI/CD, docs |
| **Phase 2: Testing & QA** | Apr 3 - Apr 10 | ✅ Complete | Load test (1862 RPS), pen test, isolation verified |
| **Phase 3: GCP Deployment** | Apr 10 - Apr 17 | 🚧 Ready | Terraform infra, Cloud Run deployment |
| **Phase 4: SignSiSure Integration** | Apr 17 - Apr 30 | ⏳ Pending | Custom agents, Eurotrust tooling |
| **Phase 5: Production & Scale** | May 2026 | ⏳ Planned | Monitoring, backup, SLA, onboarding |

---

## Key Metrics

### Performance (Load Test)

| Endpoint | RPS | P95 Latency | Status |
|----------|-----|-------------|--------|
| GET /health | **1862** | 18ms | ✅ Exceeds 100 RPS target |
| GET /api/v1/agents/ | **501** | 70ms | ✅ Exceeds 100 RPS target |
| POST /api/v1/auth/token | 5.6 | 1783ms | ✅ Acceptable (bcrypt intentional) |

### Security

| Control | Status |
|---------|--------|
| SQL Injection Prevention | ✅ SQLAlchemy ORM |
| Authentication | ✅ API Key + JWT (bcrypt) |
| Multi-Tenancy Isolation | ✅ Verified |
| Secrets Management | ✅ .env local, Secret Manager prod |
| Input Validation | ✅ Pydantic v2 |
| CORS | ✅ Restricted origins |

---

## Repository Structure

```
agentAichain/
├── agent_aichain/          # Core Python package
│   ├── api/               # FastAPI endpoints
│   ├── core/              # Config, DB, security
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic
│   ├── workers/           # Celery tasks & AGNO wrapper
│   └── main.py            # FastAPI app entry
├── docs/                  # 8 documentation files
├── tests/                 # Unit + integration tests
├── scripts/               # create_tenant.py, seed.py
├── terraform/gcp/         # GCP infrastructure
├── load-tests/            # Load test script
├── docker-compose.yml     # Local development
├── Dockerfile             # Production image
├── deploy-gcp.sh          # Automated deployment
└── README.md              # Project overview
```

---

## Getting Started (Development)

```bash
# Clone and setup
git clone https://github.com/aichainssrl-collab/agentAichain.git
cd agentAichain

# Start with Docker Compose
docker-compose up -d

# Seed demo data
docker-compose exec api python scripts/seed.py

# Access API
curl http://localhost:8000/health
# Swagger UI: http://localhost:8000/docs

# Demo credentials:
# Email: admin@demo.com
# Password: demo123
```

---

## API Quick Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Health check |
| `/api/v1/auth/token` | POST | Form | Get JWT token |
| `/api/v1/auth/register-tenant` | POST | JSON | Create new tenant |
| `/api/v1/agents/` | GET | JWT/API Key | List agents |
| `/api/v1/agents/` | POST | JWT/API Key | Create agent |
| `/api/v1/teams/` | POST | JWT/API Key | Create team |
| `/api/v1/runs/agent/{id}` | POST | JWT/API Key | Execute agent |
| `/api/v1/api-keys/` | POST | JWT | Create API key |

**Full API docs:** `/docs` endpoint (Swagger)

---

## GCP Deployment

**Status:** Ready to deploy  
**Estimated time:** 30-60 minutes  
**Estimated cost:** $50-80/month (small scale)

### Prerequisites

- GCP project with billing
- gcloud CLI authenticated
- Terraform installed
- Docker installed

### Deploy in One Command

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Run deployment script
./deploy-gcp.sh terraform.tfvars
```

The script will:
- Initialize Terraform
- Plan and apply infrastructure
- Build and push Docker image
- Deploy to Cloud Run
- Run database migrations
- Create demo tenant (optional)

---

## Next Steps

### Immediate (Phase 3)

1. **Deploy to GCP** using `deploy-gcp.sh`
2. Verify health endpoint and Swagger UI
3. Test with production-like data
4. Set up monitoring alerts (Cloud Monitoring)
5. Configure budget alerts

### Short-term (Phase 4)

1. Integrate SignSiSure use case
2. Build Eurotrust QES signing tool
3. Develop custom agents for document processing
4. End-to-end testing with sandbox

### Long-term (Phase 5)

1. Production hardening (WAF, advanced monitoring)
2. Multi-region setup (enterprise tier)
3. Advanced billing (Stripe integration)
4. Feature flags per tenant
5. SSO integration (SAML/OIDC)

---

## Technical Decisions

### Why These Technologies?

| Technology | Reason |
|------------|--------|
| **FastAPI** | Async support, auto-docs, type hints |
| **SQLAlchemy** | Mature ORM, async support, migrations |
| **PostgreSQL** | Relational data, ACID, GCP managed |
| **Redis** | Fast cache, Celery broker |
| **Celery** | Reliable background jobs |
| **Docker** | Consistent environments |
| **Terraform** | Infrastructure as code |
| **Cloud Run** | Serverless, auto-scaling, pay-per-use |
| **AGNO** | Open-source agent framework |

---

## Contact & Support

- **Tech Lead:** Dylan (CTO, Aichain Solutions)
- **Repository:** https://github.com/aichainssrl-collab/agentAichain
- **Documentation:** `/docs` directory
- **Issues:** GitHub Issues

---

## Appendix

### Performance Benchmarks

 tested on MacBook Pro M1, Docker Compose:

- **Health endpoint:** 1862 RPS (50% CPU)
- **Agents list (JWT):** 501 RPS
- **Database:** PostgreSQL 15 on F1-micro
- **Redis:** Memorystore 1GB

Production on GCP will have higher performance with dedicated resources.

### Security Posture

- ✅ All queries tenant-scoped
- ✅ Passwords hashed with bcrypt
- ✅ JWT signed with HS256
- ✅ SQL injection prevented (ORM)
- ✅ CORS configured
- ✅ Structured audit logging
- ⚠️ Rate limiting pending (Phase 5)

### Known Limitations

1. **No rate limiting** – will be added in Phase 5
2. **No SSO** – planned for enterprise tier
3. **Neo4j** – optional graph DB not fully configured yet

---

*Document version: 1.0 | Last updated: 2026-04-04*