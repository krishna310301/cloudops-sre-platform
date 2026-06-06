# Observability

This document captures the CloudOps SRE Platform observability proof for AWS EKS.

Do not run the AWS commands until the short-lived demo environment is created.

## Observability Components

- CloudWatch Logs through the Amazon CloudWatch Observability EKS add-on
- Prometheus and Grafana through `kube-prometheus-stack`
- Metrics Server for HPA CPU metrics
- Kubernetes events and rollout status through `kubectl`

## CloudWatch Logs

The Amazon CloudWatch Observability EKS add-on installs CloudWatch Agent and Fluent Bit. AWS documents that it can collect infrastructure metrics, application telemetry, and container logs, and that container logs are collected by default.

Install instructions are in:

```text
docs/aws-addons.md
```

After installing the add-on and deploying the app, verify CloudWatch log groups:

```bash
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws logs describe-log-groups \
  --log-group-name-prefix "/aws/containerinsights/${CLUSTER_NAME}" \
  --query "logGroups[].logGroupName" \
  --output table
```

Expected log groups:

```text
/aws/containerinsights/<cluster-name>/application
/aws/containerinsights/<cluster-name>/dataplane
/aws/containerinsights/<cluster-name>/host
```

Find recent backend logs:

```bash
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws logs filter-log-events \
  --log-group-name "/aws/containerinsights/${CLUSTER_NAME}/application" \
  --filter-pattern "backend" \
  --max-items 20
```

Generate backend log traffic:

```bash
ALB_URL="http://$(kubectl get ingress -n cloudops cloudops-cloudops-sre-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"

curl "$ALB_URL/api/health"
curl "$ALB_URL/api/metrics"
curl "$ALB_URL/api/demo/cpu?duration_ms=100"
```

Capture screenshots:

- CloudWatch log group list
- Backend pod log events
- Frontend/Nginx log events if visible

## Prometheus And Grafana

Install commands are in:

```text
docs/aws-addons.md
```

Verify monitoring pods:

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Open Grafana:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Useful dashboards and views:

- Kubernetes / Compute Resources / Namespace Pods
- Kubernetes / Compute Resources / Pod
- Kubernetes / Kubelet
- Kubernetes / API server

Useful PromQL:

```promql
sum(rate(container_cpu_usage_seconds_total{namespace="cloudops"}[2m])) by (pod)
```

```promql
sum(container_memory_working_set_bytes{namespace="cloudops"}) by (pod)
```

```promql
kube_pod_container_status_restarts_total{namespace="cloudops"}
```

```promql
kube_horizontalpodautoscaler_status_current_replicas{namespace="cloudops"}
```

Capture screenshots:

- Backend CPU during k6 load
- Backend memory
- Pod restart count
- HPA current replicas

## Kubernetes Operational Checks

```bash
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
kubectl describe hpa -n cloudops cloudops-cloudops-sre-platform-backend
kubectl logs -n cloudops deploy/cloudops-cloudops-sre-platform-backend --tail=100
kubectl logs -n cloudops deploy/cloudops-cloudops-sre-platform-frontend --tail=100
kubectl get events -n cloudops --sort-by=.lastTimestamp
```

Capture screenshots:

- Pods/services/ingress/HPA overview
- HPA describe output
- Backend logs
- Recent Kubernetes events

## Evidence Checklist

- CloudWatch application log group
- Backend logs in CloudWatch
- Frontend logs in CloudWatch
- Grafana pod CPU/memory dashboard
- HPA scale-out graph
- Kubernetes `kubectl get pods,svc,ingress,hpa`
