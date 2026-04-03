output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "postgres_instance_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  value = google_redis_instance.redis.host
}

output "cloud_run_service_url" {
  value = google_cloud_run_service.api.status[0].url
}

output "artifact_bucket_name" {
  value = google_storage_bucket.artifact_bucket.name
}