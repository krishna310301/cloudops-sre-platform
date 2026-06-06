# AWS Demo Day Checklist

This checklist is for the short-lived AWS proof deployment. Do not start unless you have time to capture evidence and destroy everything the same day.

## Before Apply

- Docker local dev stack works
- Production-style local stack works
- Backend tests pass
- Frontend build passes
- Terraform validates
- Helm chart lints
- k6 smoke test passes
- AWS CLI is authenticated to the correct account
- Region is confirmed
- Budget/cost expectations are understood

Validation bundle:

```bash
docker compose exec backend pytest -q
docker compose exec frontend npm run build
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
docker run --rm -v "$PWD:/workspace" -w /workspace alpine/helm:3.15.4 lint charts/cloudops-sre-platform -f charts/cloudops-sre-platform/values-aws-example.yaml
docker run --rm -e BASE_URL="http://host.docker.internal:8080" -e TARGET_PATH="/api/demo/cpu" -e CPU_DURATION_MS="10" -e SMOKE_TEST="true" -v "$PWD/load-tests:/scripts" grafana/k6:0.54.0 run /scripts/k6-load-test.js
```

## Terraform Plan

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
terraform -chdir=infra plan
```

Review for:

- EKS cluster
- Managed node group
- RDS PostgreSQL
- NAT Gateway
- ECR repositories
- Secrets Manager secret
- IAM roles

Stop if you cannot destroy the environment the same day.

## Apply

```bash
terraform -chdir=infra apply
```

Immediately capture:

```bash
terraform -chdir=infra output
```

## Configure Cluster

```bash
AWS_REGION="$(terraform -chdir=infra output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
kubectl get nodes -o wide
```

## Install Add-Ons

Follow:

```text
docs/aws-addons.md
```

Install:

- AWS Load Balancer Controller
- Metrics Server
- CloudWatch Observability add-on
- kube-prometheus-stack

## Deploy App

Push images through GitHub Actions manual deploy or local ECR commands.

Then deploy:

```bash
kubectl create namespace cloudops --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install cloudops charts/cloudops-sre-platform \
  --namespace cloudops \
  -f charts/cloudops-sre-platform/values-aws-example.yaml \
  --set backend.image.repository="$(terraform -chdir=infra output -raw backend_ecr_repository_url)" \
  --set frontend.image.repository="$(terraform -chdir=infra output -raw frontend_ecr_repository_url)"
```

Verify:

```bash
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-frontend -n cloudops
```

## Capture Proof

Use:

```text
docs/evidence.md
docs/hpa-demo.md
docs/observability.md
```

## Destroy Same Day

Uninstall app/add-ons:

```bash
helm uninstall cloudops -n cloudops
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall metrics-server -n kube-system
helm uninstall aws-load-balancer-controller -n kube-system
aws eks delete-addon --cluster-name "$(terraform -chdir=infra output -raw cluster_name)" --addon-name amazon-cloudwatch-observability
```

Destroy:

```bash
terraform -chdir=infra destroy
```

Verify expensive resources are gone:

```bash
aws eks list-clusters
aws elbv2 describe-load-balancers
aws rds describe-db-instances
aws ec2 describe-nat-gateways
aws ec2 describe-instances
```
