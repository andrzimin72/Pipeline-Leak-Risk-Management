# terraform/modules/kubernetes/main.tf
resource "nebius_kubernetes_cluster" "pipeline" {
  name       = "${var.project_name}-${var.environment}"
  network_id = var.network_id
  
  master {
    version   = var.k8s_version
    zonal {
      zone      = "eu-central1-a"
      subnet_id = var.subnet_id
    }
    
    public_ip {
      enabled = true
    }
    
    security_group_ids = [nebius_vpc_security_group.k8s_master.id]
  }
  
  service_account_id      = nebius_iam_service_account.k8s_node.id
  node_service_account_id = nebius_iam_service_account.k8s_node.id
  
  release_channel = "REGULAR"
  
  network_policy_provider = "CALICO"
  
  kms_key {
    created_at = nebius_kms_symmetric_key.k8s_key.created_at
    id         = nebius_kms_symmetric_key.k8s_key.id
  }
}

# System Node Pool
resource "nebius_kubernetes_node_group" "system" {
  cluster_id  = nebius_kubernetes_cluster.pipeline.id
  name        = "system-pool"
  version     = var.k8s_version
  
  instance_template {
    platform_id = "standard-v3"
    
    resources {
      cores         = var.system_pool_size.cpu
      memory        = var.system_pool_size.memory
      core_fraction = 100
    }
    
    boot_disk {
      type = "network-ssd"
      size = var.system_pool_size.disk_size
    }
    
    network_interface {
      nat                 = true
      subnet_ids          = [var.subnet_id]
      security_group_ids  = [nebius_vpc_security_group.k8s_nodes.id]
    }
    
    metadata = {
      ssh-keys = "ubuntu:${file("~/.ssh/id_rsa.pub")}"
    }
  }
  
  scale_policy {
    fixed_scale {
      size = var.system_pool_size.instances
    }
  }
  
  allocation_policy {
    location {
      zone = "eu-central1-a"
    }
  }
  
  maintenance_policy {
    auto_upgrade = true
    auto_repair  = true
  }
}

# API Node Pool (CPU-optimized)
resource "nebius_kubernetes_node_group" "api" {
  cluster_id  = nebius_kubernetes_cluster.pipeline.id
  name        = "api-pool"
  version     = var.k8s_version
  
  instance_template {
    platform_id = "standard-v3"
    
    resources {
      cores         = var.api_pool_size.cpu
      memory        = var.api_pool_size.memory
      core_fraction = 100
    }
    
    boot_disk {
      type = "network-ssd"
      size = var.api_pool_size.disk_size
    }
    
    network_interface {
      nat                = true
      subnet_ids         = [var.subnet_id]
      security_group_ids = [nebius_vpc_security_group.k8s_nodes.id]
    }
  }
  
  scale_policy {
    auto_scale {
      min     = 3
      max     = 20
      initial = var.api_pool_size.instances
    }
  }
  
  allocation_policy {
    location {
      zone = "eu-central1-a"
    }
  }
}

# GPU Node Pool (for AI workloads)
resource "nebius_kubernetes_node_group" "gpu" {
  cluster_id  = nebius_kubernetes_cluster.pipeline.id
  name        = "gpu-pool"
  version     = var.k8s_version
  
  instance_template {
    platform_id = "gpu-v2"
    
    resources {
      cores  = var.gpu_pool_size.cpu
      memory = var.gpu_pool_size.memory
    }
    
    gpus {
      type = var.gpu_type
      count = var.gpu_count
    }
    
    boot_disk {
      type = "network-ssd"
      size = var.gpu_pool_size.disk_size
    }
    
    network_interface {
      nat                = true
      subnet_ids         = [var.subnet_id]
      security_group_ids = [nebius_vpc_security_group.k8s_nodes.id]
    }
  }
  
  scale_policy {
    fixed_scale {
      size = var.gpu_pool_size.instances
    }
  }
}

# Security Groups
resource "nebius_vpc_security_group" "k8s_master" {
  name       = "${var.project_name}-${var.environment}-k8s-master"
  network_id = var.network_id
  
  ingress {
    protocol       = "TCP"
    description    = "Kubernetes API"
    port           = 6443
    predefined_target = "loadbalancer_healthchecks"
  }
  
  ingress {
    protocol       = "TCP"
    description    = "Node communication"
    from_port      = 0
    to_port        = 65535
    security_group_id = nebius_vpc_security_group.k8s_nodes.id
  }
  
  egress {
    protocol       = "ANY"
    description    = "Allow all outbound"
    from_port      = 0
    to_port        = 65535
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "nebius_vpc_security_group" "k8s_nodes" {
  name       = "${var.project_name}-${var.environment}-k8s-nodes"
  network_id = var.network_id
  
  ingress {
    protocol          = "ANY"
    description       = "Node-to-node communication"
    from_port         = 0
    to_port           = 65535
    security_group_id = nebius_vpc_security_group.k8s_master.id
  }
  
  ingress {
    protocol          = "ANY"
    description       = "Node-to-node communication"
    from_port         = 0
    to_port           = 65535
    security_group_id = nebius_vpc_security_group.k8s_nodes.id
  }
  
  egress {
    protocol       = "ANY"
    description    = "Allow all outbound"
    from_port      = 0
    to_port        = 65535
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Service Accounts
resource "nebius_iam_service_account" "k8s_node" {
  name = "${var.project_name}-${var.environment}-k8s-node"
}

resource "nebius_resourcemanager_folder_iam_member" "k8s_node" {
  folder_id = var.folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${nebius_iam_service_account.k8s_node.id}"
}

# KMS Key for encryption
resource "nebius_kms_symmetric_key" "k8s_key" {
  name              = "${var.project_name}-${var.environment}-k8s-key"
  default_algorithm = "AES_256"
  rotation_period   = "8760h" # 1 year
}