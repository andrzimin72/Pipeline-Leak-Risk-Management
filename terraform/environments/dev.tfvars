# terraform/environments/dev.tfvars
project_name = "Pipeline Leak Risk Management"
environment  = "dev"
zone         = "eu-central1-a"
vpc_cidr     = "10.1.0.0/16"
k8s_version  = "1.29"

system_pool_size = {
  instances = 1
  cpu       = 2
  memory    = 4
  disk_size = 50
}

api_pool_size = {
  instances = 2
  cpu       = 4
  memory    = 8
  disk_size = 100
}

gpu_pool_size = {
  instances = 1
  cpu       = 8
  memory    = 32
  disk_size = 200
}

gpu_type       = "nvidia-l40s"
gpu_count      = 1
postgres_tier  = "s2-small"
alert_email    = "pipeline-dev@exxonmobil.com"