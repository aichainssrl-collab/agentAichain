# AgentAichain Architecture

## Overview

AgentAichain is a **multi-tenant B2B platform** for orchestrating AI agents. Built on FastAPI, SQLAlchemy, and AGNO, it provides complete tenant isolation, audit logging, and GCP-native deployment.

## Core Principles

1. **Multi-tenancy by design** – Every query is scoped to a tenant_id, enforced at the database and application layers
2. **Stateless API layer** – Horizontal scaling in Cloud Run
3. **Async-first** – Async SQLAlchemy, async HTTP requests, Celery for long-running tasks
4. **Observability** – Structured JSON logs, audit trails, Prometheus metrics
5. **Security** – API-key auth, JWT for user auth, secrets management via GCP Secret Manager

---

## System Components

### 1. FastAPI Application (`agent_aichain/main.py`)

- REST API endpoints under `/api/v1/`
- CORS enabled for web frontends
- Global exception handler with structured logging
- Health check endpoint (`/health`)
- Lifespan events for DB initialization

### 2. SQLAlchemy Models (`agent_aichain/models/`)

**Tenant Isolation:**
- `Tenant` – Top-level tenant entity
- `User` – Belongs to a tenant
- `APIKey` – Machine-to-machine auth, scoped to tenant
- `Agent` – AI agent definition (tenant-scoped)
- `Team` – Group of agents (tenant-scoped)
- `Run` – Execution record (tenant-scoped)
- Association table `team_agents` for many-to-many Agent ↔ Team

All models have `tenant_id` foreign key and relationships enforce isolation.

### 3. Database Layer

**PostgreSQL (Cloud SQL):**
- Stores all metadata
- Async connection pool via `SQLAlchemy 2.0 async`
- Alembic for migrations
- Row-level security could be added if needed

**Redis (Memorystore):**
- Celery broker (queue 1)
- Celery result backend (queue 2)
- Optional cache layer for frequent queries

**Optional Neo4j:**
- Graph memory for agent knowledge (future)

### 4. Agent & Team Execution

**TenantAwareAgent (`workers/agno_wrapper.py`):**
- Wraps AGNO Agent API
- Injects tenant context into payload
- Handles HTTP communication, timeouts, errors

**TenantAwareTeam:**
- Wraps AGNO Team API
- Serializes team composition (list of agents)
- Injects tenant metadata

**Celery Tasks (`workers/tasks.py`):**
- `run_agent_task` – Async execution via Celery
- `run_team_task` – Team execution via Celery
- Both use asyncio to run async DB operations
- Update `Run` status (pending → running → completed/failed)

### 5. Authentication & Authorization

**API Key Auth (primary for B2B):**
- Header: `X-API-Key: <key>`
- Hashed storage (bcrypt)
- Optional expiry
- Inactive revocation
- Rate limiting per key (future)

**JWT Auth (for future web UI):**
- OAuth2 password flow
- Tokens contain `sub` (user_id) and `tenant_id`
- Signed with HS256

**Current Users:**
- Simplified demo: stored in DB, hashed passwords
- Production: integrate with SSO/Okta/Auth0

### 6. Security & Isolation

**Database-level:**
- All queries filter by `tenant_id` (see API layer)
- No cross-tenant queries allowed
- Foreign keys cascade delete tenant data

**Application-level:**
- `get_current_user` and `get_current_tenant` dependencies
- API key verification endpoint middleware (TODO)
- Structured audit logging (JSON with tenant_id, user_id)

**Infrastructure-level:**
- GCP Secret Manager for secrets (not env vars in production)
- Private VPC for Cloud SQL, Redis
- Cloud Run IAM restrictions

---

## Data Flow: Create & Run Agent

```mermaid
sequenceDiagram
    Client->>+API: POST /api/v1/agents (API Key)
    API->>+DB: INSERT Agent (tenant_id=X)
    DB-->>-API: agent_id=123
    API-->>-Client: {id: 123}

    Client->>+API: POST /api/v1/agents/123/run {task…}
    API->>+DB: INSERT Run (status=pending)
    DB-->>-API: run_id=456
    API->>+Celery: run_agent_task.delay(456)
    Celery-->>-API: task_id=abc123
    API-->>-Client: {run_id: 456, task_id: abc123}

    Celery->>+DB: SELECT Agent, Tenant WHERE id=123
    DB-->>-Celery: agent, tenant
    Celery->>+AGNO: POST /agents/run (payload with tenant context)
    AGNO-->>-Celery: result
    Celery->>+DB: UPDATE Run SET status=completed, output=…
    DB-->>-Celery: OK
```

---

## Deployment Architecture (GCP)

```
┌─────────────────┐
│    Client /     │
│   Frontend      │
└────────┬────────┘
         │ HTTPS + API Key
┌────────▼──────────────┐
│ Cloud Run (stateless) │
│   agent-aichain-api   │
└────────┬──────────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌─────┐  ┌─────────┐ ┌─────┐ ┌─────────┐
│SQL  │  │  Redis  │ │GCS  │ │ Secret  │
│ Cloud│ │Memory   │ │Artif│ │ Manager │
│Store │ │store    │ │acts │ │         │
└─────┘  └─────────┘ └─────┘ └─────────┘
```

- **Cloud Run**: Auto-scaling, pay-per-use, 0 to thousands of req/s
- **Cloud SQL**: PostgreSQL with automated backups
- **Memorystore**: Redis HA (optional standard tier)
- **GCS**: Agent artifacts, logs (optional)
- **Secret Manager**: DB passwords, JWT secrets, AGNO keys
- **Cloud Monitoring**: Metrics, dashboards, alerts
- **Cloud Logging**: Structured JSON logs exported

---

## Scalability Considerations

1. **Stateless API** – All state in DB/Redis; any Cloud Run instance can handle any request
2. **Database connection pooling** – PgBouncer could be added if needed; Cloud Run respects `DATABASE_URL` pool size
3. **Celery Workers** – Separate deployment (Cloud Run jobs or GKE) with auto-scaling based on queue depth
4. **Rate Limiting** – Per-tenant per-minute limits (to be implemented via Redis counters)
5. **Caching** – Redis cache for frequent tenant/agent lookups
6. **Database Read Replicas** – For heavy read workloads (future)

---

## Multi-Tenancy Implementation Details

**Models:**

Every table has `tenant_id` (foreign key to `tenants.id`). All SELECT queries include `WHERE tenant_id = :current_tenant`. On DELETE of tenant, cascade deletes all associated data.

**Example query pattern (SQLAlchemy):**

```python
# Correct: tenant-scoped
query = select(Agent).where(
    Agent.tenant_id == current_tenant_id,
    Agent.is_active == True
)

# Wrong: unscoped (would leak cross-tenant data)
query = select(Agent).where(Agent.is_active == True)  # ❌ NEVER DO THIS
```

**API Endpoints (all require authentication):**

- Auth: `/api/v1/auth/token`, `/api/v1/auth/register-tenant`
- Agents: `/api/v1/agents/` (list, create), `/api/v1/agents/{id}` (get, delete)
- Teams: `/api/v1/teams/` (list, create), `/api/v1/teams/{id}` (get, add/remove agents)
- Runs: `/api/v1/runs/` (list), `/api/v1/runs/agent/{agent_id}` (create), `/api/v1/runs/team/{team_id}` (create)
- API Keys: `/api/v1/api-keys/` (list, create, revoke)

---

## Monitoring & Observability

**Structured Logging (JSON):**

```json
{
  "timestamp": "2026-04-03T12:34:56.789Z",
  "level": "info",
  "event": "agent_run_completed",
  "tenant_id": 42,
  "agent_id": 123,
  "tokens_used": 450,
  "duration_ms": 1234
}
```

**Prometheus Metrics (to be added):**

- `agent_runs_total` (by tenant, status)
- `agent_run_duration_seconds` (histogram)
- `api_requests_total` (by endpoint, method, status)
- `celery_tasks_active`
- `database_connections_active`

---

## Security Checklist

- [x] Secrets in GCP Secret Manager (not .env in prod)
- [x] API key hashing (bcrypt)
- [x] JWT signed with strong secret
- [x] CORS restricted to known origins
- [x] All queries tenant-scoped
- [x] Audit logging (planned in Run model)
- [ ] Rate limiting (Redis-based)
- [ ] IP allowlisting per tenant (future)
- [ ] Pen test penetration testing
- [x] Database encryption at rest (Cloud SQL default)
- [x] TLS 1.2+ enforced (Cloud Run default)

---

## Future Enhancements

- WebSocket streaming for real-time agent responses
- Neo4j integration for persistent agent memory
- Advanced billing (Stripe) with usage-based pricing per tenant
- SSO integration (SAML/OIDC)
- Multi-region failover
- Advanced RBAC (roles: admin, operator, viewer per tenant)
- Feature flags per tenant
- S3-compatible artifact storage (agent uploads, logs)

---

*Last updated: 2026-04-03*