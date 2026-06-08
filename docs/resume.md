# Resume Notes

## Project Title

CloudOps SRE Platform | EKS, Helm, ECR, RDS, Terraform, FastAPI, React

## One-Line Description

CloudOps SRE Platform is a cloud-native reliability operations dashboard built on Amazon EKS to track service health, deployments, incidents, MTTR, and SLO-style reliability metrics while demonstrating production-style Kubernetes deployment, CI/CD, autoscaling, observability, and infrastructure as code.

## Resume Bullets

- Built CloudOps SRE Platform, a cloud-native reliability operations dashboard on Amazon EKS using React, FastAPI, PostgreSQL/RDS, Docker, ECR, Helm, ALB Ingress, Terraform, and GitHub Actions.
- Implemented service catalog, deployment tracking, P1-P4 incident workflows, incident timelines, MTTR metrics, health status dashboards, and SLO-style reliability views for production operations use cases.
- Configured Kubernetes deployments, services, ingress, liveness/readiness probes, Secrets Manager integration, CloudWatch logging, HPA autoscaling, and runbooks for failed deployments, service degradation, and optional Grafana observability.

## Interview Talking Points

- Why EKS and Helm were used instead of a single EC2 deployment
- How backend HPA is triggered and proven with k6
- How ALB Ingress routes traffic to the frontend
- How the frontend proxies `/api` requests to the backend service
- How RDS is kept private
- How Secrets Manager feeds the app database URL
- How CloudWatch logs, Kubernetes events, Metrics Server, and HPA status support day-two troubleshooting
- How Grafana can be added with kube-prometheus-stack for deeper pod metrics
- How the project is designed for same-day teardown to control cost

## STAR Story Prompts

### Reliability Operations

Situation: Platform teams need one place to view service health, incidents, deployments, and MTTR.

Task: Build a cloud-native reliability dashboard that maps to real SRE workflows.

Action: Implemented FastAPI APIs, React dashboard, PostgreSQL schema, incident timelines, deployment history, and MTTR calculations.

Result: Created a portfolio project that demonstrates production operations concepts beyond a simple CRUD app.

### Kubernetes And Autoscaling

Situation: Cloud and platform roles often expect hands-on Kubernetes/EKS experience.

Task: Demonstrate deployment, probes, resources, and HPA scaling.

Action: Packaged the app with Helm, configured resource requests/limits and HPA, and added a bounded CPU endpoint plus k6 load test.

Result: The project captured scale-out/scale-in evidence with `kubectl`, Metrics Server, HPA status, and load-test screenshots, with Grafana documented as an optional add-on.

### Cost Control

Situation: EKS, RDS, NAT Gateway, and ALB can become expensive if left running.

Task: Build an AWS demo that proves skill without ongoing cost.

Action: Designed local-first validation, short-lived Terraform deployment, evidence checklist, and same-day destroy workflow.

Result: The project is ready for a controlled demo deployment with explicit cleanup verification.
