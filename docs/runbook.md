# Runbook

This runbook covers common CloudOps SRE Platform operations scenarios.

## Service Degradation

Symptoms:

- Dashboard shows degraded/down service count increasing
- Open incidents increase
- Backend health checks fail or latency rises

Initial checks:

```bash
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
kubectl get events -n cloudops --sort-by=.lastTimestamp
kubectl logs -n cloudops deploy/cloudops-cloudops-sre-platform-backend --tail=100
curl "$ALB_URL/api/health"
curl "$ALB_URL/api/metrics"
```

Actions:

1. Confirm whether frontend, backend, database, or ingress is affected.
2. Check recent deployments.
3. Open or update an incident in the CloudOps UI.
4. If backend pods are unhealthy, inspect readiness/liveness probe failures.
5. If database errors appear, check RDS status and security group connectivity.

Validation notes to capture:

- `kubectl get pods`
- backend logs
- incident timeline update
- dashboard degraded status

## Failed Deployment

Symptoms:

- Deployment page shows failed deployment
- Kubernetes rollout does not complete
- New pods are in `CrashLoopBackOff`, `ImagePullBackOff`, or not ready

Checks:

```bash
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops
kubectl describe pod -n cloudops -l app.kubernetes.io/component=backend
kubectl logs -n cloudops deploy/cloudops-cloudops-sre-platform-backend --tail=100
kubectl get events -n cloudops --sort-by=.lastTimestamp
```

Common causes:

- Wrong image tag
- Missing ECR permission
- Missing database secret
- Bad environment variable
- Probe path not reachable

Rollback option:

```bash
helm rollback cloudops -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-frontend -n cloudops
```

CloudOps UI actions:

1. Register failed deployment.
2. Open incident if user impact exists.
3. Add timeline update with suspected cause.
4. Resolve after rollback or fix is verified.

## Incident Workflow

1. Create incident with service, severity, and status.
2. Add timeline update when investigation begins.
3. Move status to `identified` when root cause is known.
4. Move status to `monitoring` after mitigation.
5. Resolve once service is stable.
6. Record MTTR from started time to resolved time.

Recommended timeline update style:

```text
15:04 UTC - CloudWatch alarm triggered for backend 5xx rate.
15:11 UTC - Identified failed deployment v1.14.2 as likely cause.
15:18 UTC - Rolled back to v1.14.1 and backend readiness recovered.
15:30 UTC - Error rate stable under threshold; incident resolved.
```

## HPA Scale-Out Validation

Use:

```bash
docs/hpa-demo.md
```

Quick checks:

```bash
kubectl get hpa -n cloudops
kubectl top pods -n cloudops
kubectl get pods -n cloudops -w
```

Expected:

- Backend HPA exists
- CPU rises during k6 load
- Backend replicas increase
- Backend replicas later scale back down

## CloudWatch Logs Validation

Use:

```bash
docs/observability.md
```

Checks:

```bash
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws logs describe-log-groups \
  --log-group-name-prefix "/aws/containerinsights/${CLUSTER_NAME}" \
  --output table
```

Expected:

- Application log group exists
- Backend and frontend pod logs are visible

## AWS Cleanup Verification

Before destroy:

```bash
helm uninstall cloudops -n cloudops
helm uninstall metrics-server -n kube-system
helm uninstall aws-load-balancer-controller -n kube-system
aws eks delete-addon --cluster-name "$(terraform -chdir=infra output -raw cluster_name)" --addon-name amazon-cloudwatch-observability
```

If Grafana was installed, also run:

```bash
helm uninstall kube-prometheus-stack -n monitoring
```

Destroy:

```bash
terraform -chdir=infra destroy
```

Verify in AWS:

- EKS cluster deleted
- RDS instance deleted
- NAT Gateway deleted
- ALB deleted
- EC2 worker nodes gone
- EBS volumes gone
- Elastic IP released

Validation notes to capture:

- Terraform destroy confirmation
- AWS console or CLI showing no EKS/RDS/ALB/NAT resources remain
