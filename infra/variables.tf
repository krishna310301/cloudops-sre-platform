variable "project_name" {
  description = "Project name used for resource names and tags."
  type        = string
  default     = "cloudops-sre-platform"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "demo"
}

variable "owner" {
  description = "Owner tag for portfolio demo resources."
  type        = string
  default     = "krishna-koushik-thokala"
}

variable "aws_region" {
  description = "AWS region for the short-lived demo deployment."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the project VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be 2 or 3."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets."
  type        = list(string)
  default     = ["10.40.0.0/24", "10.40.1.0/24", "10.40.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private EKS workload subnets."
  type        = list(string)
  default     = ["10.40.10.0/24", "10.40.11.0/24", "10.40.12.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for isolated database subnets."
  type        = list(string)
  default     = ["10.40.20.0/24", "10.40.21.0/24", "10.40.22.0/24"]
}

variable "enable_nat_gateway" {
  description = "Create one NAT Gateway so private EKS nodes can pull images and reach AWS APIs."
  type        = bool
  default     = true
}

variable "eks_cluster_version" {
  description = "Optional EKS version. Null lets AWS choose the current default supported version."
  type        = string
  default     = null
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group."
  type        = list(string)
  default     = ["t3.small"]
}

variable "node_desired_size" {
  description = "Desired number of EKS worker nodes for the demo."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of EKS worker nodes."
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of EKS worker nodes."
  type        = number
  default     = 4
}

variable "node_disk_size_gb" {
  description = "Worker node root volume size in GB."
  type        = number
  default     = 30
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "cloudops"
}

variable "db_username" {
  description = "PostgreSQL admin username."
  type        = string
  default     = "cloudops"
}

variable "db_instance_class" {
  description = "RDS instance class for the short-lived demo."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "Optional PostgreSQL engine version. Null lets AWS choose the default supported minor version."
  type        = string
  default     = null
}

variable "db_allocated_storage_gb" {
  description = "Initial RDS storage allocation in GB."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage_gb" {
  description = "Maximum RDS autoscaled storage in GB."
  type        = number
  default     = 30
}

variable "cloudwatch_log_retention_days" {
  description = "Short retention keeps demo logging costs controlled."
  type        = number
  default     = 7
}

variable "aws_load_balancer_controller_namespace" {
  description = "Namespace for the AWS Load Balancer Controller service account."
  type        = string
  default     = "kube-system"
}

variable "aws_load_balancer_controller_service_account" {
  description = "Service account name for AWS Load Balancer Controller IRSA."
  type        = string
  default     = "aws-load-balancer-controller"
}

variable "aws_load_balancer_controller_chart_version" {
  description = "AWS Load Balancer Controller Helm chart version documented for the demo."
  type        = string
  default     = "1.14.0"
}
