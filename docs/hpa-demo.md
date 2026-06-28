# HPA Demo

This runbook captures how the backend scales under CPU load on EKS.

Do not run this until:

- Terraform has created EKS
- AWS Load Balancer Controller is installed
- Metrics Server is installed
- CloudOps app is deployed with Helm
- The ALB URL is reachable
- You are ready to capture screenshots and destroy the AWS environment the same day

## 1. Verify HPA Baseline

```bash
kubectl get hpa -n cloudops
kubectl get pods -n cloudops -o wide
kubectl top pods -n cloudops
```

Expected baseline:

- HPA exists for `cloudops-cloudops-sre-platform-backend`
- Backend starts near `2` replicas
- CPU usage is low before load

Capture screenshot:

```text
kubectl get hpa -n cloudops
kubectl get pods -n cloudops -o wide
```

## 2. Find The ALB URL

```bash
ALB_URL="http://$(kubectl get ingress -n cloudops cloudops-cloudops-sre-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
echo "$ALB_URL"
```

Verify the app:

```bash
curl -I "$ALB_URL"
curl "$ALB_URL/api/health"
curl "$ALB_URL/api/demo/cpu?duration_ms=100"
```

Expected:

- App returns HTTP 200
- `/api/health` returns `status: ok`
- `/api/demo/cpu` returns `purpose: hpa-demo`

## 3. Run k6 Load Test

Smoke-test the k6 script locally before running the full HPA demo:

```bash
docker run --rm \
  -e BASE_URL="http://host.docker.internal:8080" \
  -e TARGET_PATH="/api/demo/cpu" \
  -e CPU_DURATION_MS="10" \
  -e SMOKE_TEST="true" \
  -v "$PWD/load-tests:/scripts" \
  grafana/k6:0.54.0 run /scripts/k6-load-test.js
```

Expected:

- `status is 200`
- `hpa demo response`
- `checks: 100%`

Run the full AWS load test:

Local Docker command:

```bash
docker run --rm \
  -e BASE_URL="$ALB_URL" \
  -e TARGET_PATH="/api/demo/cpu" \
  -e CPU_DURATION_MS="350" \
  -v "$PWD/load-tests:/scripts" \
  grafana/k6:0.54.0 run /scripts/k6-load-test.js
```

If k6 is installed locally:

```bash
BASE_URL="$ALB_URL" \
TARGET_PATH="/api/demo/cpu" \
CPU_DURATION_MS="350" \
k6 run load-tests/k6-load-test.js
```

## 4. Watch Scale-Out

In separate terminals:

```bash
kubectl get hpa -n cloudops -w
```

```bash
kubectl get pods -n cloudops -w
```

```bash
kubectl top pods -n cloudops
```

Expected during load:

- HPA CPU target rises above `60%`
- Backend replicas increase above baseline
- New backend pods move to `Running`

Capture screenshots:

- `kubectl get hpa -n cloudops`
- `kubectl get pods -n cloudops -o wide`
- `kubectl top pods -n cloudops`

## 5. Optional Grafana Capture

The completed AWS demo used `kubectl`, Metrics Server, CloudWatch logs, and screenshots to document HPA behavior. Use this section only if the optional Prometheus/Grafana add-on is installed.

Full install, dashboard, screenshot, and cleanup steps are in `docs/grafana-demo.md`.

Open Grafana:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Open:

```text
http://localhost:3000
```

Useful PromQL queries:

```promql
sum(rate(container_cpu_usage_seconds_total{namespace="cloudops", pod=~"cloudops-cloudops-sre-platform-backend.*", container="backend"}[2m])) by (pod)
```

```promql
kube_deployment_status_replicas_available{namespace="cloudops", deployment="cloudops-cloudops-sre-platform-backend"}
```

```promql
kube_horizontalpodautoscaler_status_current_replicas{namespace="cloudops", horizontalpodautoscaler="cloudops-cloudops-sre-platform-backend"}
```

Capture screenshots:

- Backend pod CPU increasing during load
- Backend replica count increasing
- HPA current replicas vs desired replicas

## 6. Verify Scale-In

After k6 stops, wait several minutes:

```bash
kubectl get hpa -n cloudops
kubectl get pods -n cloudops
kubectl top pods -n cloudops
```

Expected:

- CPU decreases
- HPA eventually scales backend back toward baseline

Capture screenshot:

```text
kubectl get hpa -n cloudops
kubectl get pods -n cloudops
```

## 7. Validation Checklist

- Baseline HPA before load
- k6 load test running
- Backend pod scale-out
- HPA CPU target above threshold
- `kubectl top pods` during load
- Optional Grafana CPU graph
- Optional Grafana HPA/current replicas graph
- Scale-in after load stops
