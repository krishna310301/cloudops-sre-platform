# AWS Demo Proof

This page records evidence from the short-lived AWS demo deployment of CloudOps SRE Platform. Screenshot evidence is stored in `docs/screenshots/` when captured during demo runs.

## Demo Run Summary

- Date: June 6, 2026
- AWS region: `us-east-1`
- Deployment model: short-lived Terraform apply, EKS deploy, HPA load test, same-day destroy
- Result: application deployed successfully on Amazon EKS behind an AWS Application Load Balancer
- Cleanup: Terraform destroy completed and post-destroy checks confirmed cost-bearing resources were removed

## Application Proof

Temporary ALB endpoint observed during the demo:

```text
k8s-cloudops-cloudops-30c69c9652-1264128751.us-east-1.elb.amazonaws.com
```

Health endpoint response:

```json
{"status":"ok","environment":"aws-demo"}
```

Metrics endpoint returned seeded reliability data:

```text
total services: 3
healthy services: 2
degraded/down services: 1
open incidents: 1
average MTTR: 100
failed deployments: 1
platform status: critical
```

## Kubernetes And HPA Proof

Baseline HPA state before load:

```text
backend HPA: cpu 7% / 60%, replicas 2
```

k6 load test summary:

```text
HTTP requests: 946
Failed requests: 0
Checks: 100%
p95 latency: 1.53s
Max VUs reached: 24
```

HPA state during load:

```text
backend HPA: cpu 387% / 60%, replicas 6
backend deployment: 6/6 available
backend pods: 6 running and ready
```

## Cleanup Proof

After the demo, the application and Kubernetes add-ons were uninstalled, the ALB was deleted, and Terraform destroy completed.

Post-destroy verification confirmed:

- Terraform state was empty
- EKS cluster was not found
- RDS database was not found
- ECR repositories were not found
- Application Load Balancer was not found
- Project VPC was not found
- Project Elastic IPs were not found
- NAT Gateway was in deleted state only

## Screenshot Gallery

Store sanitized screenshots in `docs/screenshots/` using the naming guide in [docs/evidence.md](evidence.md).

Recommended LinkedIn-ready images:

- Live app dashboard on ALB URL
- Services page
- Incident detail timeline
- Deployment history
- GitHub Actions successful workflow
- EKS cluster and nodes
- `kubectl get pods,svc,ingress,hpa`
- HPA scale-out during k6 load
- CloudWatch logs
- Terraform destroy confirmation

Before committing screenshots, crop or blur sensitive account IDs, secrets, private endpoint details, personal data, and unnecessary browser chrome.
