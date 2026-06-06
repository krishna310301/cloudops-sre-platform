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

This workflow does not create AWS resources.

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
- Helm lint and template render
- Terraform validate

These default jobs do not push images, deploy to EKS, or create AWS resources.

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
- You are ready to capture proof and destroy the environment the same day
