# Security Policy

AgentAichain is designed with security as a priority. This document outlines security practices, threat model, and compliance considerations.

---

## Threat Model

**What we protect:**
1. **Tenant data isolation** – Prevent data leakage between tenants
2. **API credentials** – API keys and JWT tokens
3. **PII** – Personal data stored in DB (user emails, etc.)
4. **Agent execution environment** – Safe execution of potentially malicious tools/code
5. **Infrastructure** – GCP resources, secrets, network

**Attack vectors:**
- Stolen API key / credential leak
- SQL injection or NoSQL injection
- Cross-tenant data access (bugs in scoping)
- DDoS / rate limiting bypass
- RCE via agent tools (future concern)
- Supply chain compromise (dependencies)

---

## Multi-Tenancy & Data Isolation

### Implementation

1. **Database schema:** Every table has `tenant_id` NOT NULL
2. **Foreign keys:** Cascade delete from tenant
3. **Query scoping:** All API endpoints filter by `tenant_id` derived from authentication
4. **Service layer:** TenantService enforces ownership

**Example pattern:**

```python
# In API endpoint
@router.get("/agents")
async def list_agents(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # USES tenant_id from current_user
    result = await db.execute(
        select(Agent).where(Agent.tenant_id == current_user.tenant_id)
    )
```

### Validation

- Unit tests verify tenant isolation (`tests/integration/test_tenancy.py`)
- Penetration test will attempt to access cross-tenant data
- Code review checklist includes "tenant_id check"

---

## Authentication & Authorization

### API Keys (M2M)

- Random 32-byte URL-safe tokens
- Hashed with bcrypt (stored in DB)
- Can be scoped by:
  - Read-only vs read-write (future)
  - Expiry date
  - IP allowlist (future)

### JWT (User Auth)

- Issued after password verification
- Contains: `sub` (user_id), `tenant_id`, `exp`
- Signed with HS256 using strong secret
- Expires after 30 minutes (configurable)

Future: Refresh tokens with rotation.

### Password Policy

- Minimum length: 12 characters
- Bcrypt work factor: 12 (adjustable)
- No password complexity rules (NIST recommendation)

---

## Secrets Management

### Development

- `.env.example` as template
- `.env` in `.gitignore`
- **Never** commit secrets

### Production (GCP)

All secrets in **Secret Manager**:

| Secret | Purpose |
|--------|---------|
| `agent-aichain-db-password` | PostgreSQL password |
| `agent-aichain-jwt-secret` | JWT signing key |
| `agent-aichain-agno-api-key` | AGNO service key |

Access required by:
- Cloud Run service identity (`roles/secretmanager.secretAccessor`)
- Cloud Build (for deployments)

**Rotation:**
- DB password: rotate quarterly, update Cloud Run env
- JWT secret: rotate with zero-downtime (dual-sign during transition – future)
- AGNO key: rotate immediately if leaked

---

## Network Security

### GCP VPC

- **Private IP** for Cloud SQL (no public IP)
- **VPC connector** for Cloud Run to access VPC resources
- **Firewall rules**:
  - Deny all ingress to Redis except from Cloud Run CIDR block
  - No external access to Redis

### Cloud Run

- HTTPS only (TLS 1.2+)
- IAM-based invocation (optional, we use API keys)
- VPC egress (to reach Cloud SQL, Redis)

### DDoS Protection

- Cloud Armor (to be enabled in production)
- Rate limiting at Cloud Load Balancer (future)
- Per-tenant rate limits in application (future)

---

## Encryption

**At rest:**
- Cloud SQL: AES-256 (Google-managed)
- Persistent disks: AES-256
- Secret Manager: Cloud KMS

**In transit:**
- All external traffic: TLS 1.2+
- Internal VPC traffic: encrypted by Google network
- Redis connections: TLS (enabled by default on Memorystore)

---

## Input Validation & Injection Prevention

### SQL Injection

- SQLAlchemy ORM (parameterized queries)
- Never string-interpolate user input into queries
- Example of **bad** code (DO NOT USE):
  ```python
  # ❌ VULNERABLE
  query = f"SELECT * FROM agents WHERE name = '{user_input}'"
  ```
- Example of **good** code:
  ```python
  # ✅ SAFE
  query = select(Agent).where(Agent.name == user_input)
  ```

### Command Injection

- Validate and sanitize any user-provided shell commands (none currently)
- Future agent tools that execute code: run in sandbox (Docker container)

---

## Logging & Auditing

### Structured JSON Logs

All logs include:
- `timestamp` (ISO 8601)
- `level` (INFO, WARN, ERROR)
- `tenant_id` (when available)
- `user_id` (when authenticated)
- `event` (action being performed)

Example:
```json
{
  "timestamp": "2026-04-03T12:00:00Z",
  "level": "info",
  "event": "agent_created",
  "tenant_id": 1,
  "user_id": 2,
  "agent_id": 123,
  "agent_name": "Support Bot"
}
```

### Audit Trail

**Current (Run model):**
- `Run` table stores:
  - `task` (what agent/team executed)
  - `input` (snapshot of input data)
  - `output` (agent response)
  - `tokens_used`, `cost`, `duration_ms`
  - `status` (success/failure)
  - `metadata` (tenant_id, agent_id, etc.)
  - `created_at`, `updated_at`

**Future:**
- Separate `AuditLog` table for all CRUD operations
- Immutable after creation
- Retention: 10+ years (compliance)

---

## Compliance

### GDPR

- **Data minimization:** API keys, Run inputs/outputs are personal data only if they contain PII (varies by use case)
- **Right to be forgotten:** Can delete tenant → cascades deleting all data
- **Data portability:** Export tenant data as JSON (future feature)
- **Consent:** Customer's responsibility (they use our platform to process end-user data)

### SOC 2

- **Security:** Access controls, encryption, monitoring
- **Availability:** Cloud Run SLA (99.95%), Cloud SQL SLA (99.95%)
- **Processing integrity:** Audit logs, immutability of runs
- **Confidentiality:** Network isolation, encryption
- **Privacy:** Limited data collection (only operational)

We will pursue SOC 2 Type II certification after production launch.

---

## Vulnerability Management

### Dependencies

- `pip-audit` or `safety` CI scan for known CVEs
- Dependabot/renovate for automated updates
- Quarterly security review

### Penetration Testing

- Before production launch
- Annually thereafter
- Scope: All public APIs, Cloud Run, DB, Redis
- Include:
  - OWASP Top 10
  - Multi-tenancy bypass attempts
  - Credential stuffing
  - SSRF in agent tools (future)

### Bug Bounty

- Future: HackerOne or similar
- Rewards for valid findings

---

## Incident Response

**Compromise scenarios:**

1. **Secret leak (GitHub):**
   - Rotate secret immediately
   - Revoke affected API keys
   - Review access logs for abuse
   - Add pre-commit hook to prevent future leaks

2. **Database breach:**
   - Rotate all API keys
   - Force password reset for all users
   - Rotate JWT secret (invalidates all tokens)
   - Notify affected tenants

3. **Cloud Run compromise:**
   - Disable service
   - Deploy patched version
   - Rotate all related credentials
   - Review IAM permissions

See [OPERATIONS.md](OPERATIONS.md) for full runbook.

---

## Security Checklist for Developers

- [ ] All queries include tenant_id filter
- [ ] No raw SQL string interpolation
- [ ] Secrets in .env, not in code
- [ ] Passwords hashed with bcrypt
- [ ] API keys never logged (masked)
- [ ] PII not in plain logs
- [ ] CORS configured correctly for environment
- [ ] Rate limiting considered for new endpoints
- [ ] Input validation on all user-provided data
- [ ] Unit tests cover tenant isolation

---

## Contact

Security issues: security@aichain.solutions (PGP key available)

PGP Fingerprint: `ABCD 1234 EF56 7890 GH12 3456 IJKL 7890 MNOP QRST`

*Last updated: 2026-04-03*