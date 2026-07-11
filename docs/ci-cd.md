# CI/CD

CloudOps SRE Platform uses GitHub Actions for validation, image builds, and gated AWS deployment.

## Workflows

### Terraform Validate

File:

```text
.github/workflows/terraform-validate.yml
```

Runs on:

- Pull requests that change `infra/**`
- Pushes to `main` that change `infra/**`
- Manual dispatch

Jobs:

- `terraform init -backend=false`
- `terraform fmt -check -recursive`
- `terraform validate`

This workflow does not create AWS resources or require access to the optional remote state backend. Remote state setup is documented in `docs/terraform-state.md`.

### CI CD

File:

```text
.github/workflows/deploy.yml
```

Runs on:

- Pull requests that change app, chart, Docker, or infra files
- Pushes to `main` that change app, chart, Docker, or infra files
- Manual dispatch

Default jobs:

- Backend tests with `pytest`
- Frontend build with `npm run build`
- Backend Docker image build
- Frontend production Docker image build
- Helm lint, template render, and kubeconform Kubernetes schema validation
- Terraform validate, cost guardrails, and Checkov Terraform security scan

These default jobs do not push images, deploy to EKS, or create AWS resources.

The Kubernetes manifest validation step renders the Helm chart with
`charts/cloudops-sre-platform/values-aws-example.yaml` and validates the output
with kubeconform in strict mode. This catches invalid Kubernetes API versions and
missing required fields before a manual AWS deployment.

The Terraform jobs run a repository cost/security guardrail script that fails
when demo resource sizes, retention, cleanup, or RDS exposure assumptions drift.
They also run Checkov against `infra/` as an advisory Terraform security scan. It reports production-hardening gaps without blocking the intentionally disposable validation environment.

## Manual AWS Deployment Gate

The AWS deployment jobs run only when the workflow is manually started with:

```text
deploy_to_aws = true
```

Gated jobs:

- Push backend and frontend images to ECR
- Sync database URL from Secrets Manager into a Kubernetes Secret
- Deploy with `helm upgrade --install`
- Run Kubernetes rollout checks
- Print pods, services, ingress, and HPA status

## Image Promotion

Manual AWS deployments publish both application images with one explicit tag, then deploy that exact tag through Helm. If `image_tag` is not provided, the workflow uses the commit SHA. For a cleaner release-style promotion, pass a readable tag such as:

```text
v2026.06.27-1
```

The workflow validates the tag against Docker tag rules, pushes:

```text
<account>.dkr.ecr.<region>.amazonaws.com/cloudops-sre-platform/backend:<image_tag>
<account>.dkr.ecr.<region>.amazonaws.com/cloudops-sre-platform/frontend:<image_tag>
```

and deploys with:

```text
backend.image.tag=<image_tag>
frontend.image.tag=<image_tag>
```

Avoid using `latest` for AWS evidence runs. A stable tag makes screenshots, rollback notes, and incident timelines easier to explain.

## Required GitHub Secrets

```text
AWS_ROLE_TO_ASSUME
AWS_DATABASE_SECRET_NAME
```

`AWS_ROLE_TO_ASSUME` should be an IAM role configured for GitHub OIDC. It needs permissions for:

- ECR login and image push
- EKS kubeconfig access
- Secrets Manager read for the database secret
- Kubernetes deployment through the EKS cluster identity

`AWS_DATABASE_SECRET_NAME` should match the Terraform-created database secret name:

```text
cloudops-sre-platform-demo/database
```

## Deployment Prerequisites

Before running the manual AWS deploy job:

- Terraform apply has created VPC, EKS, ECR, RDS, and Secrets Manager resources
- Backend and frontend ECR repositories exist
- AWS Load Balancer Controller is installed in the EKS cluster
- Metrics Server is installed for HPA CPU metrics
- The database secret contains a `database_url` key
- You are ready to capture screenshots and destroy the environment the same day

## Rollback

The Helm deploy uses `--atomic`, so a failed upgrade rolls back automatically within the workflow timeout.

For manual rollback after a bad deployment:

```bash
helm history cloudops -n cloudops
helm rollback cloudops -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops --timeout=180s
kubectl rollout status deployment/cloudops-cloudops-sre-platform-frontend -n cloudops --timeout=180s
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
```

Record the previous image tag, failed image tag, rollback revision, and verification commands in the incident timeline.
