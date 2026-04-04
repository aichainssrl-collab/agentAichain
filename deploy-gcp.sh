#!/bin/bash
#
# Deploy AgentAichain to Google Cloud Platform
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Terraform installed (>= 1.0)
# - Docker installed and configured for GCR
# - GitHub repository connected to Cloud Build (optional, for CI/CD)
#
# Usage: ./deploy-gcp.sh [var-file]
# Example: ./deploy-gcp.sh terraform.tfvars
#

set -e  # Exit on error
set -u  # Error on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform/gcp"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Command '$1' not found. Please install it."
        exit 1
    fi
}

# Main
log_info "🚀 Starting AgentAichain deployment to GCP..."
log_info ""

# Check prerequisites
log_info "Checking prerequisites..."
check_command gcloud
check_command terraform
check_command docker
log_info "✅ All prerequisites met"
log_info ""

# Load variables file
TFVARS_FILE="${1:-terraform.tfvars}"
if [ ! -f "$TFVARS_FILE" ]; then
    log_warn "Variables file '$TFVARS_FILE' not found."
    log_info "Creating example terraform.tfvars from template..."
    cp terraform/gcp/terraform.tfvars.example terraform.tfvars 2>/dev/null || true
    log_warn "Please edit terraform.tfvars with your actual values before continuing."
    log_warn "Required variables:"
    log_warn "  - project_id"
    log_warn "  - db_password"
    log_warn "  - jwt_secret"
    log_warn "  - agno_api_key"
    log_warn "  - github_owner (if using Cloud Build)"
    log_info ""
    read -p "Press Enter to continue after editing terraform.tfvars, or Ctrl+C to abort..."
fi

# Authenticate gcloud
log_info "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_warn "No active gcloud account. Running gcloud auth login..."
    gcloud auth login
fi
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
log_info "✅ Using gcloud account: $ACTIVE_ACCOUNT"
log_info ""

# Set project
log_info "Setting GCP project..."
PROJECT_ID=$(grep -E '^project_id\s*=' terraform.tfvars 2>/dev/null | cut -d'"' -f2 || echo "")
if [ -z "$PROJECT_ID" ]; then
    read -p "Enter your GCP Project ID: " PROJECT_ID
fi
gcloud config set project "$PROJECT_ID"
log_info "✅ Project set to: $PROJECT_ID"
log_info ""

# Enable APIs (quick check)
log_info "Ensuring required APIs are enabled..."
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
    logging.googleapis.com 2>/dev/null || true
log_info "✅ APIs enabled (or already enabled)"
log_info ""

# Terraform Init
log_info "Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init -upgrade
log_info "✅ Terraform initialized"
log_info ""

# Terraform Plan
log_info "Planning Terraform deployment..."
terraform plan -var-file="${SCRIPT_DIR}/terraform.tfvars" -out=tfplan
log_info "✅ Terraform plan created"
log_info ""

# Ask for confirmation
read -p "Do you want to apply this plan? This will create resources and incur costs. (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_warn "Deployment aborted."
    exit 0
fi

# Terraform Apply
log_info "Applying Terraform plan..."
terraform apply tfplan
log_info "✅ Infrastructure deployed"
log_info ""

# Get outputs
log_info "Retrieving deployment outputs..."
POSTGRES_CONNECTION=$(terraform output -raw postgres_instance_connection_name 2>/dev/null || echo "")
REDIS_HOST=$(terraform output -raw redis_host 2>/dev/null || echo "")
CLOUD_RUN_URL=$(terraform output -raw cloud_run_service_url 2>/dev/null || echo "")
ARTIFACT_BUCKET=$(terraform output -raw artifact_bucket_name 2>/dev/null || echo "")

log_info "  PostgreSQL Connection: $POSTGRES_CONNECTION"
log_info "  Redis Host: $REDIS_HOST"
log_info "  Cloud Run URL: $CLOUD_RUN_URL"
log_info "  Artifact Bucket: $ARTIFACT_BUCKET"
log_info ""

# Build and push Docker image
log_info "Building Docker image..."
cd "$SCRIPT_DIR"
docker build -t "gcr.io/${PROJECT_ID}/agent-aichain:latest" .
log_info "✅ Docker image built"

log_info "Pushing to Google Container Registry..."
docker push "gcr.io/${PROJECT_ID}/agent-aichain:latest"
log_info "✅ Docker image pushed"
log_info ""

# Deploy to Cloud Run (if not using Terraform's Cloud Run resource)
# Note: Terraform already deploys Cloud Run if the resource is included.
# But we might need to run migrations.
if [ -n "$CLOUD_RUN_URL" ]; then
    log_info "Cloud Run service URL: $CLOUD_RUN_URL"
    log_info ""

    # Run database migrations
    log_info "Running database migrations..."
    gcloud run services execute agent-aichain --region "$(terraform output -raw region 2>/dev/null || echo "europe-west1")" -- alembic upgrade head
    log_info "✅ Migrations applied"
    log_info ""

    # Create initial tenant (optional)
    read -p "Do you want to create a demo tenant? (yes/no): " CREATE_DEMO
    if [ "$CREATE_DEMO" = "yes" ]; then
        read -p "Enter admin email: " DEMO_EMAIL
        read -s -p "Enter admin password: " DEMO_PASSWORD
        echo
        log_info "Creating demo tenant..."
        gcloud run services execute agent-aichain --region "$(terraform output -raw region 2>/dev/null || echo "europe-west1")" -- python scripts/create_tenant.py \
            --name "Demo" \
            --slug "demo" \
            --email "$DEMO_EMAIL" \
            --password "$DEMO_PASSWORD"
        log_info "✅ Demo tenant created"
    fi

    log_info ""
    log_info "🎉 Deployment complete!"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Test health endpoint: curl $CLOUD_RUN_URL/health"
    log_info "  2. Access Swagger docs: $CLOUD_RUN_URL/docs"
    log_info "  3. Create API keys via UI or API"
    log_info ""
else
    log_warn "Cloud Run URL not available. Check Terraform outputs."
fi

# Final notes
log_info "📋 Don't forget to:"
log_info "  - Set up monitoring alerts in Cloud Monitoring"
log_info "  - Configure budget alerts in GCP Billing"
log_info "  - Review IAM permissions (least privilege)"
log_info "  - Rotate default secrets"
log_info ""
log_info "✅ Deployment script finished!"