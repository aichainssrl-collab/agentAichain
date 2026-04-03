# GCP Infrastructure Terraform Configuration

This directory contains Terraform configurations to deploy AgentAichain on Google Cloud Platform.

## Prerequisites

- Terraform >= 1.0
- gcloud CLI installed and authenticated
- GitHub repository connected to Cloud Build

## Variables

Create a `terraform.tfvars` file:

```hcl
project_id     = "your-gcp-project-id"
region         = "europe-west1"
db_password    = "your-db-password"
jwt_secret     = "your-jwt-secret-min-32-chars"
agno_api_key   = "your-agno-api-key"
github_owner   = "your-github-org"
github_repo    = "agentAichain"
```

## Deployment Steps

1. **Authenticate with GCP**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable required APIs**
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

3. **Initialize Terraform**
   ```bash
   cd terraform/gcp
   terraform init
   ```

4. **Plan**
   ```bash
   terraform plan -var-file=terraform.tfvars -out=tfplan
   ```

5. **Apply**
   ```bash
   terraform apply tfplan
   ```

6. **Configure GitHub Secrets** (for Cloud Build)
   In your GitHub repo settings, add these secrets:
   - `GCP_PROJECT_ID`: your GCP project ID
   - `GCP_SA_KEY`: service account JSON key with Cloud Run Admin, Cloud Build, Storage, SQL Admin roles

7. **Build and Deploy**
   Either push to main branch (Cloud Build trigger) or manually:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml .
   ```

## Post-Deployment

1. Run database migrations:
   ```bash
   gcloud run services execute agent-aichain-api --region=europe-west1 -- alembic upgrade head
   ```

2. Create initial tenant:
   ```bash
   gcloud run services execute agent-aichain-api --region=europe-west1 -- python scripts/create_tenant.py --name "Your Tenant" --slug "your-tenant" --email admin@example.com --password "secure-password"
   ```

## Costs

Estimated monthly costs (as of 2026):
- Cloud Run: ~$25-50 (depends on usage)
- Cloud SQL (db-f1-micro): ~$7
- Memorystore (1GB): ~$20
- Secret Manager: ~$0.06/secret/month
- Total: ~$50-80/month for small usage