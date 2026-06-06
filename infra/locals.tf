locals {
  cluster_name = "${var.project_name}-${var.environment}"
  azs          = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostControl = "destroy-same-day"
  }

  eks_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
}
