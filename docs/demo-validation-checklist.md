# Demo Validation Checklist

Use this checklist during the short AWS deployment. Capture screenshots and notes before destroying the environment.

Recommended folder:

```text
docs/screenshots/aws-demo-YYYY-MM-DD/
```

Commit sanitized screenshots to GitHub after the demo so the repo documents the EKS deployment clearly. The same images can be reused for a LinkedIn project carousel.

Suggested naming:

```text
01-live-dashboard-alb.png
02-services-page.png
03-incident-detail-timeline.png
04-deployment-history.png
05-github-actions-success.png
06-ecr-images.png
07-eks-cluster-nodes.png
08-kubectl-pods-services-ingress-hpa.png
09-hpa-before-load.png
10-hpa-during-load.png
11-hpa-after-load.png
12-cloudwatch-log-groups.png
13-cloudwatch-backend-logs.png
14-terraform-apply-output.png
15-terraform-destroy-output.png
```

## Application Screenshots

- Live app dashboard on ALB URL
- Services page with service catalog
- Incident detail page with timeline updates
- Incident resolved state with MTTR
- Deployment history page
- Metrics page if used

## AWS Screenshots

```bash
terraform -chdir=infra output
aws eks describe-cluster --name "$(terraform -chdir=infra output -raw cluster_name)"
aws ecr describe-repositories --repository-names cloudops-sre-platform/backend cloudops-sre-platform/frontend
aws rds describe-db-instances --db-instance-identifier "$(terraform -chdir=infra output -raw cluster_name)-postgres"
```

Capture:

- EKS cluster
- ECR images
- RDS instance
- ALB DNS name
- Secrets Manager database secret

## Kubernetes Screenshots

```bash
kubectl get nodes -o wide
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
kubectl describe hpa -n cloudops cloudops-cloudops-sre-platform-backend
kubectl get events -n cloudops --sort-by=.lastTimestamp
```

Capture:

- Nodes ready
- Backend/frontend pods running
- Services
- Ingress with ALB hostname
- HPA status

## CI/CD Screenshots

Capture:

- GitHub Actions workflow success
- Backend tests job
- Frontend build job
- Docker build job
- Helm validate job
- Terraform validate job
- Manual deploy job if used

## Observability Screenshots

CloudWatch:

```bash
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws logs describe-log-groups \
  --log-group-name-prefix "/aws/containerinsights/${CLUSTER_NAME}" \
  --output table
```

Minimum capture:

- CloudWatch application log group
- Backend and frontend application logs
- HPA status before, during, and after k6 load
- Pod count during scale-out

Optional Grafana capture:

- Backend CPU during k6 load
- Backend memory
- HPA current replicas
- Pod count during scale-out

## Cleanup Record

After `terraform destroy`, capture:

```bash
aws eks list-clusters
aws elbv2 describe-load-balancers
aws rds describe-db-instances
aws ec2 describe-nat-gateways
aws ec2 describe-instances
```

Expected:

- Demo EKS cluster is gone
- Demo RDS database is gone
- Demo ALB is gone
- Demo NAT Gateway is gone
- Demo worker nodes are gone
