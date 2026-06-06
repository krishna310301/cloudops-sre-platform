output "aws_region" {
  description = "AWS region used by this Terraform configuration."
  value       = var.aws_region
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.this.name
}

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs for ALB ingress."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for EKS workloads."
  value       = aws_subnet.private[*].id
}

output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL."
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL."
  value       = aws_ecr_repository.frontend.repository_url
}

output "database_secret_arn" {
  description = "Secrets Manager ARN containing database connection details."
  value       = aws_secretsmanager_secret.database_url.arn
}

output "rds_endpoint" {
  description = "RDS endpoint address."
  value       = aws_db_instance.postgres.address
}

output "oidc_provider_arn" {
  description = "EKS OIDC provider ARN for future IRSA roles."
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "aws_load_balancer_controller_role_arn" {
  description = "IRSA role ARN for the AWS Load Balancer Controller service account."
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

output "aws_load_balancer_controller_chart_version" {
  description = "Pinned AWS Load Balancer Controller Helm chart version for the demo docs."
  value       = var.aws_load_balancer_controller_chart_version
}
