# Multi-Tenancy Guide

AgentAichain implements **complete tenant isolation** – each tenant's data, agents, runs, and logs are completely separated at the application and database layers.

---

## What is Multi-Tenancy?

A **tenant** is an organization/company using AgentAichain. Multiple tenants share the same infrastructure (hardware, database, code) but cannot see each other's data.

Example:
- Tenant A: Acme Corp (id=1)
- Tenant B: Beta Inc (id=2)

Each has its own:
- Users (emails can overlap: `admin@acme.com` and `admin@beta.com`)
- Agents
- Teams
- API keys
- Run history

Database rows are linked by `tenant_id`. All queries filter by this ID.

---

## Tenant Lifecycle

### 1. Registration

Client calls `POST /api/v1/auth/register-tenant`:

```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "admin_email": "admin@acme.com",
  "admin_password": "secure_password"
}
```

**What happens:**
- Creates `Tenant` record (slug must be unique)
- Creates `User` record (admin, `is_superuser=true`)
- Returns `tenant_id` and `admin_id`

### 2. Tenant Onboarding

Admin user now:
1. Logs in via `POST /api/v1/auth/token` to get JWT (optional)
2. Creates API keys via `POST /api/v1/api-keys`
3. Shares base URL and API key with development team

### 3. Daily Operations

All API calls must include either:
- `X-API-Key: <key>` header (machine-to-machine), OR
- `Authorization: Bearer <jwt>` header (user-facing)

The system extracts `tenant_id` from:
- APIKey → `key.tenant_id`
- JWT → `payload.tenant_id`

### 4. Deletion

Delete tenant (admin operation):

```sql
DELETE FROM tenants WHERE id = 1;
-- ON DELETE CASCADE removes all related data
```

All user data, agents, runs, API keys are removed.

---

## Data Model

```
tenants
  id | name | slug | plan | ...

users
  id | email | hashed_password | tenant_id (FK) | ...

agents
  id | name | role | model | tenant_id (FK) | ...

teams
  id | name | mode | tenant_id (FK) | ...

team_agents (association)
  team_id (FK) | agent_id (FK)

runs
  id | task | status | tenant_id (FK) | agent_id (FK) | team_id (FK) | ...

api_keys
  id | name | hashed_key | tenant_id (FK) | owner_id (FK) | ...
```

**Foreign keys with `ON DELETE CASCADE`:** When a tenant is deleted, all associated data is automatically deleted.

---

## Query Enforcement

### Always Scope by Tenant

**Correct:**
```python
@router.get("/agents")
async def list_agents(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agents = await db.execute(
        select(Agent).where(Agent.tenant_id == current_user.tenant_id)
    )
    return agents.scalars().all()
```

**Wrong (data leak):**
```python
# ❌ NEVER DO THIS
agents = await db.execute(select(Agent))  # No tenant filter!
```

### Relationship Queries

When joining tables, always include tenant condition:

```python
# Get team with its agents
team = await db.execute(
    select(Team).where(
        Team.id == team_id,
        Team.tenant_id == tenant_id  # Must include!
    )
)
```

---

## Testing Multi-Tenancy

### Unit Tests

`tests/unit/test_models.py` verifies model creation with `tenant_id`.

### Integration Tests

`tests/integration/test_tenancy.py`:

1. Creates two tenants
2. Creates agents for each tenant
3. Queries agents by `tenant_id`
4. Asserts zero cross-contamination

Run:
```bash
pytest tests/integration/test_tenancy.py -v
```

---

## Common Pitfalls

### 1. Forgetting Tenant Filter

**Symptom:** Tenant A sees Tenant B's agents.

**Fix:** Double-check all SELECT queries include `tenant_id`.

### 2. Direct SQL / Raw SQL

If you must use raw SQL, always parameterize:

```python
# ✅ Good
await db.execute(
    text("SELECT * FROM agents WHERE tenant_id = :tid"),
    {"tid": tenant_id}
)

# ❌ Bad
await db.execute(f"SELECT * FROM agents WHERE tenant_id = {tenant_id}")
```

### 3. Background Tasks

Background Celery tasks must fetch `tenant_id` from DB (stored in `Run` record) – never trust client input.

### 4. Caching

Redis cache keys must include `tenant_id` prefix:

```python
# ✅ Good
cache_key = f"tenant:{tenant_id}:agents:list"

# ❌ Bad
cache_key = "agents:list"  # Collision risk!
```

---

## Multi-Tenancy by Schema (Alternative)

We chose **shared database, shared schema** with `tenant_id` column.

Alternatives considered:

| Approach | Pros | Cons |
|----------|------|------|
| Shared DB, shared schema (current) | Low cost, easy to manage | Must filter every query; harder to enforce |
| Shared DB, separate schema | Stronger isolation; easier to dump tenant data | More complex migrations; connection per tenant may hit limits |
| Separate database | Full isolation; per-tenant backups | High cost; operational overhead |

We may add schema-level separation later for enterprise customers.

---

## Tenant-Specific Configuration

Some tenants may require different settings:

- Max agents per tenant: `tenants.max_agents` (enforced on create)
- Rate limits: per-tenant config table (future)
- Feature flags: `tenants.features` JSON column (future)
- Custom AGNO model endpoints: `tenants.agno_config` (future)

---

## Monitoring Tenants

**Per-tenant metrics:**
- Agent count (vs `max_agents` limit)
- Runs per day
- API usage (per API key)
- Error rate by tenant

Grafana dashboard (future) to spot noisy tenants or abuse.

---

## Billing & Quotas

**Quotas in `tenants` table:**
- `max_agents`
- `max_teams`
- `max_runs_per_month`

**Enforcement:**
- On agent/team creation: check current count vs limit
- On run creation: increment counter; fail if limit exceeded
- Reset monthly (cron job)

**Billing plans:**
- `free`: limits above, no SLA
- `pro`: higher limits, priority support
- `enterprise`: custom limits, dedicated instance (optional)

---

## Security Considerations

- **Never** trust client-provided `tenant_id` – always derive from authenticated user or API key
- **Never** log API keys or JWT tokens
- **Never** expose one tenant's data to another via API responses
- **Always** validate resource ownership: `WHERE id = X AND tenant_id = Y`

---

## FAQ

**Q: Can a user belong to multiple tenants?**
A: Not currently. User → Tenant is 1:1. Future: invite system with multiple tenant membership.

**Q: How do I migrate a tenant to its own database?**
A: Export tenant data → new database → update connection routing (feature flag). Currently not supported.

**Q: How long is data retained?**
A: Indefinitely unless tenant deleted. Run data can be archived to GCS after 1 year (future feature).

**Q: Can I have custom domains per tenant?**
A: Cloud Run supports custom domains, but mapping is per-service, not per-tenant. For per-tenant domains, need reverse proxy (future).

---

*See also: [ARCHITECTURE.md](ARCHITECTURE.md) for technical implementation details.*