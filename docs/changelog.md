# Changelog

## Unreleased - SRE Hardening Pass

Release date: pending

This update strengthens the project as an SRE/platform portfolio system by
turning the AWS demo baseline into a more operationally mature codebase.

### Added

- Structured JSON backend logging with `X-Request-ID` request correlation,
  request latency/status fields, and service/incident/deployment event context
- Alembic migration scaffolding, initial schema migration, Docker Compose
  migration startup, and a Helm pre-install/pre-upgrade migration Job
- Kubernetes manifest validation in CI with Helm render plus kubeconform
- Terraform cost/security guardrail checks and advisory Checkov scans in CI
- SLO and error budget metrics in the API and frontend Metrics view
- Frontend loading, retry, failed-refresh, and pending-action states
- RDS connectivity and secret rotation runbook for AWS demo operations

### Validated

- Backend API tests: `9 passed`
- Frontend production build
- Helm lint and render for AWS values
- Workflow YAML parsing
- Terraform formatting and cost/security guardrail script

### Notes

- External Secrets/IRSA, release promotion, and optional Grafana screenshots
  remain future hardening items.

## v1.0.0 - AWS Demo Baseline

Release date: June 8, 2026

This release marks the CloudOps SRE Platform baseline after the short-lived AWS deployment and same-day teardown.

### Added

- React frontend and FastAPI backend for service health, incidents, timelines, deployments, MTTR, and reliability metrics
- PostgreSQL schema and seeded local demo data
- Docker Compose development stack and production-style Nginx/FastAPI/PostgreSQL stack
- Terraform AWS foundation for VPC, EKS, ECR, RDS PostgreSQL, IAM, Secrets Manager, CloudWatch, and security groups
- Helm chart for Kubernetes Deployments, Services, ALB Ingress, ConfigMap/Secret usage, probes, resource limits, and backend HPA
- GitHub Actions validation for backend tests, frontend build, Docker builds, Helm lint/render, and Terraform validation
- k6 HPA load-test script and `/demo/cpu` endpoint for controlled autoscaling validation
- AWS demo screenshot gallery covering ALB app access, EKS nodes, ECR images, Kubernetes resources, HPA scale-out, CloudWatch logs, Terraform apply, and Terraform destroy
- Optional Terraform S3 remote-state documentation and backend template

### Validated

- Local development stack
- Production-style local Docker stack
- Backend unit tests
- Frontend production build
- Terraform formatting and validation
- Helm chart lint/render workflow
- Short-lived AWS deployment on Amazon EKS
- HPA scale-out under k6 load
- Same-day AWS cleanup and cost-bearing resource verification

### Notes

- Prometheus/Grafana remains an optional observability add-on path, documented separately from the completed AWS demo baseline.
- The AWS deployment is intended for short demo runs, not always-on hosting.
