# Operations & Runbook

Operational guide for running AgentAichain in production on GCP.

---

## Monitoring & Alerting

### Cloud Monitoring Metrics

**Custom Metrics (to be implemented):**

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|-----------------|
| `agent_aichain/runs/active` | Gauge | Currently executing runs | > 100 |
| `agent_aichain/runs/completed_total` | Counter | Successful runs | – |
| `agent_aichain/runs/failed_total` | Counter | Failed runs | Rate > 5% over 5m |
| `agent_aichain/api_requests_total` | Counter | All API requests | – |
| `agent_aichain/api_errors_total` | Counter | 5xx responses | Rate > 1% over 5m |
| `agent_aichain/tenant_count` | Gauge | Active tenants | – |
| `agent_aichain/celery_queue_length` | Gauge | Tasks in queue | > 100 |
| `agent_aichain/db_connections_active` | Gauge | Active DB connections | > 80% of max |
| `agent_aichain/run_duration_seconds` | Histogram | Agent/team execution time | p95 > 60s |

**Infrastructure Metrics (GCP native):**
- Cloud Run instance count, CPU, memory
- Cloud SQL connections, storage, CPU
- Redis memory usage, connections

### Alerting Policies

Create alerts in Cloud Monitoring:

```yaml
alerts:
  - name: "High API Error Rate"
    condition: metric.type="agent_aichain/api_errors_total" rate(5m) / metric.type="agent_aichain/api_requests_total" rate(5m) > 0.01
    notification_channels: [email, slack]

  - name: "Celery Queue Backlog"
    condition: metric.type="agent_aichain/celery_queue_length" > 100 for 5m
    auto_close: 1h

  - name: "Cloud Run High Latency"
    condition: metric.type="run.googleapis.com/request_latencies" p95 > 10s for 5m
    severity: critical

  - name: "Database Connections High"
    condition: metric.type="cloudsql.googleapis.com/database/cpu/utilization" > 0.8 for 10m
```

---

## Logging

### Structured Log Format

All Python logs use `structlog` JSON format. Example:

```json
{
  "timestamp": "2026-04-03T12:34:56.789Z",
  "level": "info",
  "event": "agent_run_completed",
  "tenant_id": 42,
  "agent_id": 123,
  "run_id": 456,
  "tokens_used": 450,
  "duration_ms": 2340,
  "message": "Agent run completed successfully"
}
```

### Cloud Logging Queries

**All errors for a specific tenant:**
```
resource.type="cloud_run_revision"
jsonPayload.tenant_id="42"
jsonPayload.level="error"
```

**Failed runs:**
```
resource.type="cloud_run_revision"
jsonPayload.event="run_failed"
```

**Slow runs (>30s):**
```
resource.type="cloud_run_revision"
jsonPayload.event="agent_run_completed"
jsonPayload.duration_ms>30000
```

---

## Backup & Restore

### Cloud SQL Automated Backups

- Enabled by default (7-day retention)
- Daily at 2 AM local time
- Point-in-time recovery (PITR) enabled

**Manual backup:**
```bash
gcloud sql backups create --instance=agent-aichain-db
```

**Restore:**
```bash
gcloud sql backups restore --instance=agent-aichain-db --backup=BACKUP_ID
```

### Redis Backup

Redis Memorystore does not have native backups. For production:
- Enable persistence (AOF) – slight performance impact
- Use `redis-cli --rdb` to export RDB file to GCS via Cloud Run job (custom script)

### Database Migration Backups

Before running `alembic upgrade`:

```bash
# Export schema + data
gcloud sql export sql agent-aichain-db gs://BUCKET/backup_$(date +%Y%m%d).sql --database=agent_aichain

# Or use pg_dump via Cloud Shell
pg_dump -h $(gcloud sql instances describe agent-aichain-db --format='value(connectionName)') -U postgres agent_aichain > backup.sql
```

---

## Incident Response

### Incident: High Error Rate

**Symptoms:**
- Cloud Monitoring alert: `agent_aichain/api_errors_total` > 1% over 5m
- Increased 5xx responses in logs

**Steps:**
1. Check Cloud Run Revision metrics → CPU, memory, latency
2. Check Cloud SQL CPU/connections → DB overload?
3. Check recent deployments → Rollback if new release
4. Check logs for stack traces: `resource.type="cloud_run_revision" severity=ERROR`
5. If DB issue, failover to read replica (if configured) or restart instance
6. If code bug, create hotfix and deploy

**Escalation:**
- Platform Engineer on-call
- Notify CTO if >30 min

---

### Incident: Data Breach / Leak

**Immediate:**
1. **Isolate:** Disable Cloud Run service:
   ```bash
   gcloud run services update-traffic agent-aichain-api --to-revisions=0
   ```
2. **Rotate credentials:**
   - All API keys: bulk revoke via script
   - JWT secret: generate new, deploy
   - AGNO API key: rotate externally
3. **Investigate:** Search logs for data access outside tenant boundaries
   ```bash
   gcloud logging read 'jsonPayload.tenant_id:*' --freshness=1h --format=json > suspicious.json
   ```
4. **Notify:** Legal, customers (per GDPR 72h)
5. **Fix:** Deploy tenant-scoping patch, audit code
6. **Restore:** After verification, re-enable traffic

---

### Incident: AGNO API Outage

**Symptoms:**
- Celery tasks failing with connection errors to `api.agno.io`
- Runs stuck in `running` or failing with timeouts

**Steps:**
1. Check AGNO status page / status.twitter.com
2. If AGNO down, enable degradation mode:
   - Mark new runs as `failed` with message "AGNO service unavailable"
   - Return cached responses if available (future)
3. Communicate status to customers via status page
4. When AGNO recovers, drain backlog (scale up Celery workers)
5. Consider circuit breaker pattern for future resilience

---

### Incident: Database Unavailable

**Symptoms:**
- Cloud Run instances show high latency or 503s
- Logs: `connection timeout` to Cloud SQL

**Steps:**
1. Check Cloud SQL instance status:
   ```bash
   gcloud sql instances describe agent-aichain-db
   ```
2. If stopped, start instance:
   ```bash
   gcloud sql instances patch agent-aichain-db --activation-policy=ALWAYS
   ```
3. If maintenance, wait for completion
4. If disk full, increase size:
   ```bash
   gcloud sql instances patch agent-aichain-db --database-version=POSTGRES_15 --tier=db-f1-micro --storage-size=20GB
   ```
5. If connection pool exhausted, increase max_connections in Cloud SQL flags

---

### Incident: Celery Worker Down

**Symptoms:**
- New agent/team runs stuck in `pending`
- No new `running` runs appearing
- Flower (if deployed) shows 0 workers

**Steps:**
1. Check Celery worker logs:
   ```bash
   gcloud run services list  # if deployed as service
   gcloud logging tail -s celery-worker
   ```
2. Restart worker:
   ```bash
   gcloud run services replace deployment.yaml  # redeploy
   # or if on GKE: kubectl rollout restart deployment/celery-worker
   ```
3. Check Redis connectivity (Celery broker)
4. Scale up workers temporarily:
   ```bash
   gcloud run services update-traffic agent-aichain-api --region=europe-west1 --max-instances=20
   ```
5. Drain stuck tasks: Celery `revoke` command or wait for timeout

---

## Routine Maintenance

### Daily
- Check Cloud Monitoring for anomalies
- Review error logs (5xx rate)
- Verify backups ran (Cloud SQL)

### Weekly
- Review cost reports (GCP Billing)
- Check tenant growth (active tenants metric)
- Review fat queries (slow log)

### Monthly
- Rotate secrets (API keys, JWT, passwords)
- Run security scans: `pip-audit` in CI
- Review IAM permissions (least privilege)
- Test disaster recovery restore
- Update dependencies (security patches)

---

## CI/CD Pipeline

### GitHub Actions Workflow

`.github/workflows/ci.yml`:

1. **On PR to main:**
   - Run lint (ruff)
   - Type check (mypy)
   - Unit tests (pytest)
   - Integration tests (docker-compose)
   - Build Docker image

2. **On merge to main:**
   - Push to Docker Hub (or GCR)
   - Deploy to staging (manual approval)
   - Run smoke tests
   - Deploy to production (manual approval)

### Rolling Deployments

Cloud Run automatically does blue-green:
1. New revision created
2. Traffic split (100% to new after health check)
3. Old revision kept for rollback

**Zero-downtime deploy:**
```bash
gcloud run deploy agent-aichain-api --image gcr.io/PROJECT/agent-aichain:tag --region=europe-west1 --platform=managed
```

### Database Migrations

Never automatic in prod. Manual:

```bash
# 1. Schedule maintenance window
# 2. Run migration
gcloud run services execute agent-aichain-api --region=europe-west1 -- alembic upgrade head
# 3. Verify
curl https://api.example.com/health
# 4. Monitor for 1 hour
```

---

## Scaling

### Vertical Scaling (Bigger instances)

```bash
gcloud run services update agent-aichain-api \
  --cpu 2 \
  --memory 2Gi \
  --region=europe-west1
```

### Horizontal Scaling (More instances)

```bash
gcloud run services update agent-aichain-api \
  --min-instances 1 \
  --max-instances 50 \
  --region=europe-west1
```

**Concurrency:** Adjust `--concurrency` flag (default 80). Higher = fewer instances but potentially higher latency.

---

## Security Operations

### Credential Rotation

**API Keys:**
- Rotate quarterly or upon employee departure
- Use `POST /api-keys/` create new, test, then delete old

**JWT Secret:**
- Requires dual-sign period: support both old and new secret for 1 week
- Update in Secret Manager, redeploy to pick up changes

**Database Password:**
- Update in Cloud SQL
- Update Secret Manager
- Redeploy Cloud Run

### Access Reviews

Quarterly IAM audit:
```bash
# List all Cloud Run invokers
gcloud run services get-iam-policy agent-aichain-api --region=europe-west1
# Remove unused service accounts
```

---

## Troubleshooting Cheatsheet

### "Cannot connect to database"

Check:
1. Cloud SQL instance status
2. Cloud Run env `DATABASE_URL` (use Secret Manager)
3. VPC connector (if using private IP)
4. Service account has `cloudsql.client` role

### "Redis connection refused"

Check:
1. Memorystore instance status
2. Internal IP address
3. VPC firewall rules (allow from Cloud Run CIDR)
4. Redis auth (not used by default)

### "Celery tasks not executing"

Check:
1. Workers deployed? `celery -A agent_aichain.workers.celery_app inspect active`
2. Redis broker connectivity
3. Worker logs for crashes
4. Queue name matches (`celery` default)

### "High latency on /runs endpoints"

Likely AGNO API slow → Check AGNO status
Or DB lock → Check pg_stat_activity

### "Memory OOM in Cloud Run"

Increase memory: `--memory 1Gi` or `2Gi`
Profile agent responses – maybe returning huge data

---

## Cost Optimization

- **Cloud Run:** Set `--min-instances=0` for spiky workloads (cold starts OK)
- **Cloud SQL:** Use `db-f1-micro` (free tier), enable auto-stop for non-prod
- **Redis:** 1GB is usually enough; scale down if memory < 50% used
- **Celery:** Use Cloud Run Jobs to save money vs always-on workers
- **Logging:** Set retention to 30 days (default) not indefinite

---

## Capacity Planning

**Expected load per tenant:**
- Light (free): 100 runs/month, < 10 agents
- Medium (pro): 5000 runs/month, < 50 agents
- Heavy (enterprise): 50000+ runs/month, 100+ agents

**Sizing for 100 medium tenants:**
- Cloud Run: 10-20 instances (peak @ 2.0 vCPU, 1Gi each)
- Cloud SQL: `db-g1-small` (1 vCPU, 1.7Gi RAM, 100 connections)
- Redis: `redis-standard-1` (1 vCPU, 1GB)
- Estimated monthly cost: ~$300-500 (excluding AGNO usage)

---

## Disaster Recovery

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 24 hours (daily backups)

**Recovery Steps:**
1. Provision new GCP project (or reuse DR project)
2. Restore Cloud SQL from backup or PITR
3. Recreate Redis from latest snapshot (if available) or start empty
4. Deploy Cloud Run revision
5. Update DNS / load balancer to point to new service
6. Notify customers of downtime

**Note:** Multi-region deployment not yet implemented. Will be added for enterprise tier.

---

## Support Contacts

- **On-call:** Check PagerDuty
- **Engineering:** #agent-aichain-dev Slack
- **Customer Success:** support@aichain.solutions
- **Escalation:** CTO (cto@aichain.solutions)

---

*Last updated: 2026-04-03*