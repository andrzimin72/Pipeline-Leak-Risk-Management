# terraform/outputs.tf
output "infrastructure_summary" {
  value = {
    api_endpoint       = "https://api.pipeline.${var.environment}.exxonmobil.nebius.cloud"
    dashboard_endpoint = "https://dashboard.pipeline.${var.environment}.exxonmobil.nebius.cloud"
    mqtt_endpoint      = module.network.mqtt_load_balancer_ip
    k8s_cluster_id     = module.kubernetes.cluster_id
    postgres_endpoint  = module.storage.postgres_endpoint
    bucket_name        = module.storage.artifact_bucket_name
  }
}