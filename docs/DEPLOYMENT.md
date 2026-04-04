# Deployment Guide – GCP (Cloud Run)

This guide covers deploying AgentAichain to Google Cloud Platform using Terraform and Cloud Run.

**Latest updates (Phase 2):**
- Settings Management APIs (Skills, AI Models)
- React Frontend integration
- Model validation for agents
- JWT errors improved, token expiry set to 24h

---

## Prerequisites

- GCP project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed
- GitHub repository (private or public)
- Service account with permissions:
  - Cloud Run Admin
  - Cloud SQL Admin
  - Redis Admin
  - Storage Admin
  - Secret Manager Admin
  - Service Account User

---

## Option 1: Manual Deployment

### 1. Build and Push Docker Image

```bash
# Authenticate Docker to GCR
gcloud auth configure-docker

# Build image (from project root)
docker build -t gcr.io/YOUR_PROJECT_ID/agent-aichain:latest .

# Push
docker push gcr.io/YOUR_PROJECT_ID/agent-aichain:latest
```

### 2. Create Cloud SQL Instance

```bash
gcloud sql instances create agent-aichain-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-west1 \
  --root-password=YOUR_DB_PASSWORD
```

Create database:
```bash
gcloud sql databases create agent_aichain --instance=agent-aichain-db
```

Create user:
```bash
gcloud sql users create agent_aichain --instance=agent-aichain-db --password=YOUR_DB_PASSWORD
```

### 3. Create Memorystore (Redis)

```bash
gcloud redis instances create agent-aichain-redis \
  --size=1 \
  --region=europe-west1 \
  --redis-version=redis_7 \
  --network=default
```

Get Redis IP:
```bash
gcloud redis instances describe agent-aichain-redis --region=europe-west1
```

### 4. Store Secrets in Secret Manager

```bash
# Database password
echo -n "YOUR_DB_PASSWORD" | gcloud secrets create agent-aichain-db-password --data-file=-

# JWT secret (use openssl rand -base64 32)
echo -n "YOUR_JWT_SECRET" | gcloud secrets create agent-aichain-jwt-secret --data-file=-

# AGNO API key
echo -n "YOUR_AGNO_KEY" | gcloud secrets create agent-aichain-agno-api-key --data-file=-
```

### 5. Deploy to Cloud Run

```bash
gcloud run deploy agent-aichain-api \
  --image gcr.io/YOUR_PROJECT_ID/agent-aichain:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://agent_aichain:YOUR_DB_PASSWORD@YOUR_INSTANCE_CONNECTION_NAME/agent_aichain?host=/cloudsql/YOUR_PROJECT_ID:europe-west1:agent-aichain-db" \
  --set-env-vars "REDIS_URL=redis://REDIS_IP:6379/0" \
  --set-env-vars "CELERY_BROKER_URL=redis://REDIS_IP:6379/1" \
  --set-env-vars "CELERY_RESULT_BACKEND=redis://REDIS_IP:6379/2" \
  --set-secrets="SECRET_KEY=agent-aichain-jwt-secret:latest" \
  --set-secrets="AGNO_API_KEY=agent-aichain-agno-api-key:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s
```

**Important environment variables:**
- `ACCESS_TOKEN_EXPIRE_MINUTES=1440` (default, 24h) – adjust as needed
- `LOG_LEVEL=INFO` – set to `DEBUG` for troubleshooting
- `CORS_ORIGINS=["https://your-frontend.com"]` – add your frontend URL

### 6. Run Database Migrations

```bash
gcloud run services execute agent-aichain-api --region europe-west1 -- alembic upgrade head
```

This creates all tables including the new `skills` and `ai_models` tables.

### 7. Create Initial Tenant

```bash
gcloud run services execute agent-aichain-api --region europe-west1 -- python scripts/create_tenant.py --name "Demo" --slug demo --email admin@example.com --password "secure_password"
```

### 8. Deploy Celery Workers (Optional but Recommended)

```bash
gcloud run deploy agent-aichain-worker \
  --image gcr.io/YOUR_PROJECT_ID/agent-aichain:latest \
  --region europe-west1 \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars "DATABASE_URL=..." \
  --set-env-vars "REDIS_URL=..." \
  --set-secrets="SECRET_KEY=..." \
  --set-secrets="AGNO_API_KEY=..." \
  --command "celery" \
  --args "-A agent_aichain.workers.celery_app worker --loglevel=info"
```

---

## Option 2: Terraform Deployment (Recommended)

See `terraform/gcp/README.md` for full instructions.

Quick steps:

```bash
cd terraform/gcp

# Create terraform.tfvars with your values
cat > terraform.tfvars <<EOF
project_id     = "your-gcp-project"
region         = "europe-west1"
db_password    = "your-secure-db-password"
jwt_secret     = "your-jwt-secret-min-32-characters"
agno_api_key   = "your-agno-key"
github_owner   = "your-github-org"
EOF

terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -auto-approve
```

Wait ~15 minutes for all resources.

---

## Post-Deployment

### Initialize Settings

After deployment, you should:

1. **Create Skills** (optional, but useful for agent templates):
   ```bash
   curl -X POST https://YOUR_API_URL/api/v1/settings/skills \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"name":"search_kb","description":"Search knowledge base","category":"search"}'
   ```

2. **Configure AI Models**:
   ```bash
   curl -X POST https://YOUR_API_URL/api/v1/settings/models \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "name":"gpt-4",
       "provider":"openai",
       "api_key":"sk-...",
       "max_tokens":4096,
       "max_context":8192,
       "is_active":true
     }'
   ```

   For OpenRouter, Ollama, or custom providers, set `base_url` accordingly.

3. **Create an API Key** for the frontend:
   ```bash
   curl -X POST https://YOUR_API_URL/api/v1/api-keys/ \
     -H "X-API-Key: ADMIN_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"name":"Frontend App","expires_in_days":90}'
   ```

### Deploy Frontend (Optional)

The React frontend can be deployed separately:

1. Build the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. Deploy to:
   - **Cloud Storage + CDN**: Upload `dist/` to a bucket, enable public access
   - **Netlify/Vercel**: Connect GitHub repo, set build command `npm run build`
   - **Firebase Hosting**: `firebase init hosting`, `firebase deploy`

3. Configure CORS:
   - Backend's `CORS_ORIGINS` should include your frontend URL
   - Example: `CORS_ORIGINS=["https://your-frontend.web.app"]`

### Verify Installation

- Health check: `curl https://YOUR_URL/health`
- API docs: `https://YUR_URL/docs`
- Frontend: `https://your-frontend.web.app`

---

## Environment Variables Reference

| Variable | Description | Default / Example |
|----------|-------------|-------------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://IP:6379/0` |
| `CELERY_BROKER_URL` | Celery broker (Redis DB 1) | `redis://IP:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery results (Redis DB 2) | `redis://IP:6379/2` |
| `SECRET_KEY` | JWT signing secret (from Secret Manager) | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry (default 1440 = 24h) | `1440` |
| `AGNO_API_KEY` | AGNO service key (from Secret Manager) | Required |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON) | `["http://localhost:3000"]` |

---

## Troubleshooting

### Migrations fail with "asyncpg driver not found"
Make sure `alembic.ini` has:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```
And use `asyncpg` driver in `DATABASE_URL`.

### Celery workers can't connect to Redis
Check that `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to correct Redis IP and DB numbers (1 and 2).

### 401 Unauthorized on frontend
- Verify JWT token is not expired (default 24h)
- Check `SECRET_KEY` matches between backend and token issuer
- Ensure API key is valid and active

### Model not found error when creating agent
- Verify model exists in `/settings/models` endpoint
- Check `is_active=true` on the model
- Create models via Settings API before creating agents

---

## Rollback

To rollback to previous version:

```bash
gcloud run deploy agent-aichain-api \
  --image gcr.io/YOUR_PROJECT_ID/agent-aichain:previous-tag \
  ...
```

Or use Terraform to manage versions explicitly.

---

*Based on `docs/DEPLOYMENT.md` v1.0 | Updated: 2026-04-04*

### 1. Access Your API

Get Cloud Run service URL:

```bash
gcloud run services describe agent-aichain-api --region europe-west1 --format="value(status.url)"
```

Test health endpoint:
```bash
curl https://YOUR_URL/health
```

### 2. View Logs

```bash
gcloud logs tail -s agent-aichain-api --region=europe-west1
```

Or view in Cloud Console → Logging → Logs Explorer.

### 3. Set Up Monitoring

Create alerts in Cloud Monitoring:
- Cloud Run instance count > 5 (unexpected spike)
- Error rate > 1% (5m window)
- Database connections > 80% of max
- Celery queue length > 100

---

## Environment Variables Reference

| Variable | Description | Required | Production Notes |
|----------|-------------|----------|-----------------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | Use Cloud SQL IAM or password auth |
| `REDIS_URL` | Redis connection | Yes | Memorystore internal IP |
| `CELERY_BROKER_URL` | Celery Redis broker | Yes | Separate Redis DB (1) |
| `CELERY_RESULT_BACKEND` | Celery result backend | Yes | Separate Redis DB (2) |
| `SECRET_KEY` | JWT signing secret | Yes | Min 32 bytes, rotate periodically |
| `AGNO_API_KEY` | AGNO service API key | Yes | Store in Secret Manager |
| `AGNO_BASE_URL` | AGNO endpoint URL | No | Default: https://api.agno.io |
| `LOG_LEVEL` | Logging level (INFO, DEBUG) | No | Use INFO in prod |
| `CORS_ORIGINS` | Allowed CORS origins | No | Set to your frontend URLs |

---

## Scaling Considerations

- **Min instances:** Set to 1 for low latency (avoid cold starts). Cost: ~$7/month.
- **Max instances:** Set based on expected load. Default 100, can go to 1000.
- **CPU:** Always allocate at least 1 vCPU for CPU-bound agent work.
- **Memory:** 512Mi minimum; 1Gi if agents return large responses.
- **Concurrency:** Default 80 requests per instance. Adjust if CPU or memory bound.

---

## Updating the Service

```bash
# Build and push new image
docker build -t gcr.io/PROJECT/agent-aichain:VERSION .
docker push gcr.io/PROJECT/agent-aichain:VERSION

# Deploy new version
gcloud run deploy agent-aichain-api --image gcr.io/PROJECT/agent-aichain:VERSION --region europe-west1

# Run migrations if needed
gcloud run services execute agent-aichain-api --region europe-west1 -- alembic upgrade head
```

---

## Troubleshooting

**Database connection errors:**
- Check Cloud SQL proxy is enabled on Cloud Run (set `--add-cloudsql-instances`)
- Verify service account has `cloudsql.client` role
- Check VPC connector (if using private IP)

**Redis connection errors:**
- Ensure Redis instance is in same region
- Check VPC firewall allows Cloud Run → Redis on port 6379
- Use internal IP, not external

**Migration failing:**
- Check database user has ALTER/DROP/CREATE permissions
- Ensure DB is reachable from Cloud Run

**High latency:**
- Increase CPU allocation
- Set min-instances=1 to keep warm instance
- Check AGNO API latency (may be external bottleneck)

**Celery tasks not executing:**
- Deploy Celery workers separately (Cloud Run jobs or GKE)
- Verify Redis broker connectivity
- Check worker logs

---

## Rollback

If new deployment has issues:

```bash
gcloud run services update-traffic agent-aichain-api \
  --region europe-west1 \
  --to-revisions=OLD_REVISION_NAME=100
```

Or redeploy previous image tag.

---

## Cost Optimization

- Use `db-f1-micro` (free tier eligible) for small tenants
- Set `min-instances=0` for non-critical APIs (cold starts acceptable)
- Use Cloud Run concurrency > 80 if CPU/memory allows
- Enable automatic Cloud SQL backups (7 days default) and set deletion policy
- Use Preemptible VMs for Celery workers (if occasional task loss acceptable)
- Set budget alerts in Cloud Billing

---

*See also: [docs/OPERATIONS.md](OPERATIONS.md) for runbooks and incident response.*