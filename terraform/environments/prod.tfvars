# terraform/environments/prod.tfvars
project_name = "Pipeline Leak Risk Management"
environment  = "prod"
zone         = "eu-central1-a"
vpc_cidr     = "10.0.0.0/16"
k8s_version  = "1.29"

system_pool_size = {
  instances = 3
  cpu       = 4
  memory    = 8
  disk_size = 100
}

api_pool_size = {
  instances = 5
  cpu       = 8
  memory    = 16
  disk_size = 200
}

gpu_pool_size = {
  instances = 2
  cpu       = 16
  memory    = 64
  disk_size = 500
}

gpu_type       = "nvidia-a100"
gpu_count      = 1
postgres_tier  = "s2-medium"
alert_email    = "pipeline-alerts@exxonmobil.com"