# terraform/main.tf
# ==============================================================================
# Pipeline Leak Risk Management Physical AI Platform - Nebius AI Cloud Infrastructure
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    nebius = {
      source  = "nebius-cloud/nebius"
      version = "~> 0.100.0"
    }
  }
  
  backend "s3" {
    bucket         = "pipeline-ai-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "nebius" {
  zone = var.zone
}

# ==============================================================================
# Data Sources
# ==============================================================================
data "nebius_compute_disk" "ubuntu_2204" {
  name = "ubuntu-2204-lts"
}

# ==============================================================================
# Network Infrastructure
# ==============================================================================
module "network" {
  source = "./modules/network"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

# ==============================================================================
# Kubernetes Cluster
# ==============================================================================
module "kubernetes" {
  source = "./modules/kubernetes"
  
  project_name       = var.project_name
  environment        = var.environment
  network_id         = module.network.vpc_id
  subnet_id          = module.network.subnet_id
  k8s_version        = var.k8s_version
  
  # Node pools
  system_pool_size   = var.system_pool_size
  api_pool_size      = var.api_pool_size
  gpu_pool_size      = var.gpu_pool_size
  
  # GPU configuration for AI workloads
  gpu_type           = var.gpu_type
  gpu_count          = var.gpu_count
}

# ==============================================================================
# Storage
# ==============================================================================
module "storage" {
  source = "./modules/storage"
  
  project_name = var.project_name
  environment  = var.environment
  
  # Database for risk assessments and audit logs
  postgres_version = "15"
  postgres_tier    = var.postgres_tier
  
  # Object storage for model artifacts
  bucket_name      = "${var.project_name}-${var.environment}-artifacts"
}

# ==============================================================================
# Secrets Management
# ==============================================================================
resource "nebius_lockbox_secret" "api_credentials" {
  name = "${var.project_name}-${var.environment}-api-credentials"
}

resource "nebius_lockbox_secret_version" "api_credentials_v1" {
  secret_id = nebius_lockbox_secret.api_credentials.id
  
  entries {
    key        = "NEBIUS_API_KEY"
    text_value = var.nebius_api_key
  }
  
  entries {
    key        = "SAP_AUTH_TOKEN"
    text_value = var.sap_auth_token
  }
}

# ==============================================================================
# Monitoring Stack
# ==============================================================================
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name       = var.project_name
  environment        = var.environment
  kubernetes_cluster = module.kubernetes.cluster_id
  
  grafana_admin_password = var.grafana_admin_password
  alert_email            = var.alert_email
}

# ==============================================================================
# Outputs
# ==============================================================================
output "api_endpoint" {
  value = "https://api.pipeline.${var.environment}.exxonmobil.nebius.cloud"
}

output "dashboard_endpoint" {
  value = "https://dashboard.pipeline.${var.environment}.exxonmobil.nebius.cloud"
}

output "mqtt_endpoint" {
  value = module.network.mqtt_load_balancer_ip
}

output "kubernetes_cluster_id" {
  value = module.kubernetes.cluster_id
}