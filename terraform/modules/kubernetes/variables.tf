# terraform/modules/kubernetes/variables.tf
variable "project_name" { type = string }
variable "environment" { type = string }
variable "network_id" { type = string }
variable "subnet_id" { type = string }
variable "k8s_version" { type = string }
variable "folder_id" { type = string }

variable "system_pool_size" {
  type = object({
    instances = number
    cpu       = number
    memory    = number
    disk_size = number
  })
}

variable "api_pool_size" {
  type = object({
    instances = number
    cpu       = number
    memory    = number
    disk_size = number
  })
}

variable "gpu_pool_size" {
  type = object({
    instances = number
    cpu       = number
    memory    = number
    disk_size = number
  })
}

variable "gpu_type" { type = string }
variable "gpu_count" { type = number }

output "cluster_id" {
  value = nebius_kubernetes_cluster.pipeline.id
}