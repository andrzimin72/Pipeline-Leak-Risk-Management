# terraform/variables.tf
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "Pipeline Leak Risk Management"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "zone" {
  description = "Nebius availability zone"
  type        = string
  default     = "eu-central1-a"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "k8s_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.29"
}

variable "system_pool_size" {
  description = "System node pool configuration"
  type = object({
    instances  = number
    cpu        = number
    memory     = number
    disk_size  = number
  })
  default = {
    instances = 3
    cpu       = 4
    memory    = 8
    disk_size = 100
  }
}

variable "api_pool_size" {
  description = "API node pool configuration"
  type = object({
    instances  = number
    cpu        = number
    memory     = number
    disk_size  = number
  })
  default = {
    instances = 5
    cpu       = 8
    memory    = 16
    disk_size = 200
  }
}

variable "gpu_pool_size" {
  description = "GPU node pool for AI workloads"
  type = object({
    instances  = number
    cpu        = number
    memory     = number
    disk_size  = number
  })
  default = {
    instances = 2
    cpu       = 16
    memory    = 64
    disk_size = 500
  }
}

variable "gpu_type" {
  description = "GPU type for AI workloads"
  type        = string
  default     = "nvidia-a100"
  validation {
    condition     = contains(["nvidia-a100", "nvidia-h100", "nvidia-l40s"], var.gpu_type)
    error_message = "GPU type must be A100, H100, or L40S."
  }
}

variable "gpu_count" {
  description = "Number of GPUs per node"
  type        = number
  default     = 1
}

variable "postgres_tier" {
  description = "PostgreSQL tier"
  type        = string
  default     = "s2-small"
}

variable "nebius_api_key" {
  description = "Nebius API key for LLM inference"
  type        = string
  sensitive   = true
}

variable "sap_auth_token" {
  description = "SAP authentication token"
  type        = string
  sensitive   = true
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email for critical alerts"
  type        = string
  default     = "pipeline-alerts@exxonmobil.com"
}