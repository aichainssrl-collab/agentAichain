terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "sql-component.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudtasks.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ])

  service = each.key
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "agent-aichain-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "agent-aichain-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "agent-aichain-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "database" {
  name     = "agent_aichain"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "user" {
  name     = "agent_aichain"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Cloud Memorystore (Redis)
resource "google_redis_instance" "redis" {
  name               = "agent-aichain-redis"
  memory_size_gb     = 1
  location_id        = var.region
  authorized_network = google_compute_network.vpc.id
  redis_version      = "REDIS_7"

  display_name = "Redis for AgentAichain"

  depends_on = [google_project_service.services]
}

# Secret Manager for sensitive data
resource "google_secret_manager_secret" "db_password" {
  secret_id = "agent-aichain-db-password"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "agent-aichain-jwt-secret"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

resource "google_secret_manager_secret" "agno_api_key" {
  secret_id = "agent-aichain-agno-api-key"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "agno_api_key_version" {
  secret      = google_secret_manager_secret.agno_api_key.id
  secret_data = var.agno_api_key
}

# Cloud Storage for artifacts
resource "google_storage_bucket" "artifact_bucket" {
  name     = "agent-aichain-artifacts-${random_id.bucket_suffix.hex}"
  location = var.region
  force_destroy = false
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Cloud Run service
resource "google_cloud_run_service" "api" {
  name     = "agent-aichain-api"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/agent-aichain:latest"
        env {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://agent_aichain:${var.db_password}@/${google_sql_database.database.name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
        }
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.redis.host}:6379/0"
        }
        env {
          name  = "CELERY_BROKER_URL"
          value = "redis://${google_redis_instance.redis.host}:6379/1"
        }
        env {
          name  = "CELERY_RESULT_BACKEND"
          value = "redis://${google_redis_instance.redis.host}:6379/2"
        }
        env {
          name  = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name  = "AGNO_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.agno_api_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name  = "AGNO_BASE_URL"
          value = "https://api.agno.io"
        }
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
      }
      container_concurrency = 80
      timeout_seconds      = 300
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.services,
    google_sql_database.database,
    google_redis_instance.redis
  ]
}

resource "google_cloud_run_service_iam_member" "noauth" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Build configuration
resource "google_cloudbuild_trigger" "main" {
  name        = "agent-aichain-build"
  description = "Build and deploy on push to main"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "main"
    }
  }

  substitutions = {
    _REGION = var.region
    _IMAGE  = "gcr.io/${var.project_id}/agent-aichain"
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["build", "-t", "${_IMAGE}:latest", "."]
    }
    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["push", "${_IMAGE}:latest"]
    }
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run", "deploy", "agent-aichain-api",
        "--image", "${_IMAGE}:latest",
        "--region", var.region,
        "--platform", "managed",
        "--allow-unauthenticated"
      ]
    }
  }
}