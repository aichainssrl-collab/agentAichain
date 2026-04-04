# Phase 3: GCP Deployment – Step-by-Step Guide

This guide walks through deploying AgentAichain to Google Cloud Platform using Terraform and Cloud Run.

---

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **Terraform** installed: https://developer.hashicorp.com/terraform/downloads
4. **Docker** installed and logged in to GCR: `gcloud auth configure-docker`
5. **GitHub repository** (optional for CI/CD)

---

## Step 1: Prepare Configuration

### 1.1 Create `terraform.tfvars`

Copy the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id     = "your-gcp-project-id"
region         = "europe-west1"
db_password    = "generate-a-strong-password"
jwt_secret     = "generate-a-32-char-secret"
agno_api_key   = "your-agno-service-key"
github_owner   = "your-github-username"
github_repo    = "agentAichain"
```

**Generate secrets:**
```bash
# JWT secret (32+ random chars)
openssl rand -base64 32

# DB password (min 16 chars)
openssl rand -base64 16
```

### 1.2 Enable Required APIs

Once (per project):

```bash
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  sql-component.googleapis.com \
  compute.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

---

## Step 2: Deploy Infrastructure with Terraform

### 2.1 Initialize Terraform

```bash
cd terraform/gcp
terraform init -upgrade
```

Expected output: `Terraform has been successfully initialized.`

### 2.2 Review Plan

```bash
terraform plan -var-file=../terraform.tfvars
```

Review the planned resources:
- VPC network
- Cloud SQL (PostgreSQL)
- Memorystore (Redis)
- Secret Manager secrets
- Cloud Storage bucket
- Cloud Run service
- Cloud Build trigger (optional)

### 2.3 Apply Plan

```bash
terraform apply -var-file=../terraform.tfvars
```

Type `yes` when prompted.

**Wait ~10-15 minutes** for all resources to be created.

### 2.4 Capture Outputs

After apply, note the outputs:

```bash
terraform output
```

Important outputs:
- `postgres_instance_connection_name`
- `redis_host`
- `cloud_run_service_url`
- `artifact_bucket_name`

---

## Step 3: Build and Push Docker Image

### 3.1 Build locally

```bash
cd /path/to/agentAichain
docker build -t gcr.io/YOUR_PROJECT_ID/agent-aichain:latest .
```

### 3.2 Push to GCR

```bash
docker push gcr.io/YOUR_PROJECT_ID/agent-aichain:latest
```

---

## Step 4: Deploy to Cloud Run

**Note:** Terraform already creates a Cloud Run service. If you want to trigger a new deployment manually:

```bash
gcloud run deploy agent-aichain-api \
  --image gcr.io/YOUR_PROJECT_ID/agent-aichain:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://agent_aichain:YOUR_DB_PASSWORD@/agent_aichain?host=/cloudsql/YOUR_PROJECT_ID:$REGION:agent-aichain-db" \
  --set-env-vars "REDIS_URL=redis://$REDIS_HOST:6379/0" \
  --set-env-vars "CELERY_BROKER_URL=redis://$REDIS_HOST:6379/1" \
  --set-env-vars "CELERY_RESULT_BACKEND=redis://$REDIS_HOST:6379/2" \
  --set-secrets "SECRET_KEY=agent-aichain-jwt-secret:latest" \
  --set-secrets "AGNO_API_KEY=agent-aichain-agno-api-key:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s
```

**Replace placeholders:**
- `YOUR_PROJECT_ID`
- `YOUR_DB_PASSWORD` (from terraform.tfvars)
- `$REGION` (e.g., `europe-west1`)
- `$REDIS_HOST` (from terraform output `redis_host`)

---

## Step 5: Initialize Database

Run Alembic migrations inside the Cloud Run container:

```bash
gcloud run services execute agent-aichain-api --region $REGION -- alembic upgrade head
```

---

## Step 6: Create Initial Tenant

Use the seed script to create a demo tenant:

```bash
gcloud run services execute agent-aichain-api --region $REGION -- python scripts/create_tenant.py \
  --name "Demo Tenant" \
  --slug "demo" \
  --email "admin@demo.com" \
  --password "YOUR_SECURE_PASSWORD"
```

**Save the credentials!**

---

## Step 7: Verify Deployment

### 7.1 Health Check

```bash
CLOUD_RUN_URL=$(terraform output -raw cloud_run_service_url)
curl $CLOUD_RUN_URL/health
```

Expected: `{"status":"healthy",...}`

### 7.2 Swagger UI

Open in browser:
```
$CLOUD_RUN_URL/docs
```

### 7.3 Test Authentication

```bash
# Get token
TOKEN=$(curl -s -X POST $CLOUD_RUN_URL/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@demo.com&password=YOUR_SECURE_PASSWORD" | jq -r .access_token)

# List agents
curl -H "Authorization: Bearer $TOKEN" $CLOUD_RUN_URL/api/v1/agents/
```

---

## Step 8: CI/CD (Optional)

If you set `github_owner` and `github_repo` in terraform.tfvars, Terraform creates a Cloud Build trigger.

### 8.1 Connect GitHub Repo

1. Go to Cloud Console → Cloud Build → Triggers
2. Link your GitHub repository
3. The trigger will auto-deploy on push to `main`

### 8.2 Manual Cloud Build

```bash
gcloud builds submit --config=cloudbuild.yaml .
```

---

## Step 9: Post-Deployment

### 9.1 Set Up Monitoring

Create alerts in Cloud Monitoring:
- Error rate > 1% (5m)
- Latency p95 > 1000ms
- Instance count > 10 (unexpected spike)
- Database connections > 80%

### 9.2 Budget Alerts

In GCP Billing → Budgets & Alerts, set:
- Budget amount (monthly)
- Alert at 50%, 80%, 90%, 100%
- Email notifications

### 9.3 IAM Review

Apply least privilege:
- Cloud Run service account: only necessary roles
- Remove unnecessary service account keys

---

## Troubleshooting

### Cloud SQL Connection Errors

**Symptom:** `Connection timeout` or `could not connect to server`

**Fix:**
- Ensure Cloud SQL Proxy is enabled on Cloud Run: `--add-cloudsql-instances`
- Or use private IP properly with VPC connector

### Redis Connection Refused

**Symptom:** `Redis connection refused`

**Fix:**
- Check VPC firewall allows Cloud Run CIDR to Redis (port 6379)
- Use internal IP of Redis instance
- Ensure Redis instance is in same region

### Migrations Fail

**Symptom:** `permission denied` on database

**Fix:**
- Ensure Cloud SQL user has `CREATEDB` privilege
- Run migrations as Cloud Run service with proper service account

### High Latency

**Symptom:** Requests taking > 5s

**Fix:**
- Check AGNO API latency (external dependency)
- Increase Cloud Run CPU/memory
- Enable min-instances=1 to avoid cold starts

---

## Cost Optimization Tips

- Use `db-f1-micro` (free tier eligible) for small tenants
- Set `min-instances=0` for non-critical APIs
- Enable auto-scaling with appropriate max
- Set up budget alerts
- Use preemptible VMs for Celery workers (if acceptable)

---

## Rollback

If new deployment fails:

```bash
# Revert to previous revision
gcloud run services update-traffic agent-aichain-api \
  --region $REGION \
  --to-revisions=OLD_REVISION_NAME=100
```

Or manually redeploy previous image tag.

---

## Next Phase

After successful deployment:

1. Run load test against production endpoint
2. Perform penetration test
3. Set up audit logging (BigQuery export)
4. Implement rate limiting
5. Prepare runbook for incidents

---

*Last updated: 2026-04-04*