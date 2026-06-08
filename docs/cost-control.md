# Cost Control

This project is designed for a short AWS demo deployment. Keep the AWS environment running only long enough to capture screenshots and validate the platform.

## Expensive Resources To Destroy

- EKS cluster
- EC2 worker nodes
- RDS PostgreSQL
- NAT Gateway
- Application Load Balancer
- EBS volumes created by workloads

## Terraform Cost Guardrails

The Terraform defaults are designed for a short demo:

- One NAT Gateway only
- Two `t3.small` EKS worker nodes by default
- One `db.t4g.micro` RDS PostgreSQL instance
- No RDS Multi-AZ
- No RDS deletion protection
- No final snapshot on destroy
- CloudWatch log retention set to 7 days
- Secrets Manager recovery window set to 0 days for immediate cleanup

Before any AWS apply, run:

```bash
terraform plan
```

Review the plan for these resources:

- `aws_eks_cluster`
- `aws_eks_node_group`
- `aws_db_instance`
- `aws_nat_gateway`
- `aws_eip`
- `aws_ecr_repository`
- `aws_secretsmanager_secret`
- `aws_cloudwatch_log_group`

Do not apply if you cannot destroy the environment the same day.

## Add-On Cleanup

Before `terraform destroy`, uninstall add-ons that may create AWS resources or Kubernetes resources with finalizers:

```bash
helm uninstall cloudops -n cloudops
helm uninstall metrics-server -n kube-system
helm uninstall aws-load-balancer-controller -n kube-system

aws eks delete-addon \
  --cluster-name "$(terraform -chdir=infra output -raw cluster_name)" \
  --addon-name amazon-cloudwatch-observability
```

If Grafana was installed, also run:

```bash
helm uninstall kube-prometheus-stack -n monitoring
```

Then check that the ALB created by the app ingress is gone before destroying the VPC.

## Cleanup Verification

After `terraform destroy`, confirm these are gone in the AWS console or CLI:

- EKS cluster
- RDS database
- EC2 instances
- Load balancers
- NAT gateways
- ECR images you no longer need
