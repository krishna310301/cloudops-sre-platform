# Optional Grafana Demo

This runbook is for an expanded observability pass after the main AWS demo is already working. Keep it optional so the standard run stays short and cost-controlled.

Do not start this path until:

- Terraform has created the EKS cluster
- Metrics Server is installed
- The CloudOps Helm release is healthy
- You are ready to capture screenshots and destroy the AWS environment the same day

## Install kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update prometheus-community

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --version 86.1.0 \
  --set alertmanager.enabled=false \
  --set prometheus.prometheusSpec.retention=6h \
  --set prometheus.prometheusSpec.retentionSize=4GB \
  --set grafana.service.type=ClusterIP
```

Verify:

```bash
kubectl get pods,svc -n monitoring
kubectl rollout status deployment/kube-prometheus-stack-grafana -n monitoring --timeout=180s
```

Expected:

- Prometheus Operator pods are `Running`
- Prometheus pod is `Running`
- Grafana deployment is available

## Open Grafana

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Open:

```text
http://localhost:3000
```

Get the admin password:

```bash
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Dashboard Targets

Use the built-in Kubernetes dashboards first:

- Kubernetes / Compute Resources / Namespace Pods
- Kubernetes / Compute Resources / Pod
- Kubernetes / Kubelet
- Kubernetes / API server

Useful PromQL checks:

```promql
sum(rate(container_cpu_usage_seconds_total{namespace="cloudops", pod=~"cloudops-cloudops-sre-platform-backend.*", container="backend"}[2m])) by (pod)
```

```promql
sum(container_memory_working_set_bytes{namespace="cloudops", pod=~"cloudops-cloudops-sre-platform-backend.*"}) by (pod)
```

```promql
kube_horizontalpodautoscaler_status_current_replicas{namespace="cloudops", horizontalpodautoscaler="cloudops-cloudops-sre-platform-backend"}
```

```promql
kube_horizontalpodautoscaler_status_desired_replicas{namespace="cloudops", horizontalpodautoscaler="cloudops-cloudops-sre-platform-backend"}
```

## Screenshot Checklist

Capture:

- `kubectl get pods,svc -n monitoring`
- Grafana login screen
- Backend pod CPU during k6 load
- Backend pod memory during k6 load
- HPA current replicas and desired replicas
- CloudOps namespace pod restart count
- Scale-in view after load stops

Store screenshots under:

```text
docs/screenshots/aws-demo-YYYY-MM-DD/
```

Update that folder's `README.md` with:

- What was installed
- Which dashboard or PromQL query each screenshot shows
- When the add-on was uninstalled

## Cleanup

Before destroying Terraform-managed infrastructure, remove kube-prometheus-stack:

```bash
helm uninstall kube-prometheus-stack -n monitoring
kubectl delete namespace monitoring
```

Verify no monitoring pods remain:

```bash
kubectl get pods -n monitoring
```

Then continue with the normal AWS cleanup flow in `docs/cost-control.md`.
