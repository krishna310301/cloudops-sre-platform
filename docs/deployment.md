# Deployment

## Current Status

The project is validated locally through:

- Development Docker Compose on `http://localhost:5173`
- Production-style Docker Compose on `http://localhost:8080`
- Backend API smoke tests
- Frontend production build
- Terraform formatting and validation

## Terraform Validation Only

Run these commands from the repository root:

```bash
terraform -chdir=infra init -backend=false
terraform -chdir=infra fmt -recursive
terraform -chdir=infra validate
```

Expected validation output:

```text
Success! The configuration is valid.
```

Do not run `terraform apply` until the AWS deployment checklist is complete.

## Terraform State Mode

The repository defaults to local Terraform state for the same-day AWS demo workflow. State files are ignored by git and should never be committed.

For a team-style or longer-lived deployment, use the optional S3 backend template:

```text
infra/backend.tf.example
```

Remote state setup and cleanup notes are documented in:

```text
docs/terraform-state.md
```

## Planned AWS Deployment Flow

1. Confirm AWS CLI credentials and target AWS account.
2. Review `infra/terraform.tfvars.example`.
3. Copy it to `infra/terraform.tfvars`.
4. Run `terraform plan`.
5. Review estimated resources and cost.
6. Run `terraform apply` only when ready to create the short-lived demo.
7. Build and push backend/frontend images to ECR.
8. Deploy application Helm chart to EKS.
9. Capture demo screenshots.
10. Run `terraform destroy` the same day.

## GitHub Actions

CI/CD workflow details are documented in:

```text
docs/ci-cd.md
```

Automatic validation does not deploy to AWS. ECR push and EKS deployment require a manual workflow dispatch with `deploy_to_aws=true`.

## EKS Add-Ons

Before deploying the app chart to EKS, install and verify:

- AWS Load Balancer Controller
- Metrics Server
- Amazon CloudWatch Observability add-on
- Optional kube-prometheus-stack for Grafana dashboards

Commands are documented in:

```text
docs/aws-addons.md
```

## Helm Validation Only

The chart lives at:

```text
charts/cloudops-sre-platform
```

Validate the chart without a Kubernetes cluster:

```bash
docker run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  alpine/helm:3.15.4 lint charts/cloudops-sre-platform
```

Expected output:

```text
1 chart(s) linted, 0 chart(s) failed
```

Render the AWS-style manifests locally:

```bash
docker run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  alpine/helm:3.15.4 template cloudops charts/cloudops-sre-platform \
  -f charts/cloudops-sre-platform/values-aws-example.yaml \
  --namespace cloudops
```

Expected manifest kinds include:

- `ServiceAccount`
- `ConfigMap`
- `Service`
- `Deployment`
- `HorizontalPodAutoscaler`
- `Ingress`
- Helm test `Pod`

Do not run `helm upgrade --install` until EKS, ECR images, database secret, and AWS Load Balancer Controller are ready.
