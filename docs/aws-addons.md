# AWS EKS Add-Ons

This document prepares the Kubernetes add-ons needed after Terraform creates the short-lived AWS demo cluster.

Do not run these commands until:

- `terraform apply` has completed successfully
- `aws eks update-kubeconfig` works
- ECR images exist
- You are ready to capture proof and destroy the environment the same day

## Source Versions

The AWS Load Balancer Controller instructions are pinned to the versions referenced in the Amazon EKS user guide:

- AWS Load Balancer Controller release: `v2.14.1`
- AWS Load Balancer Controller Helm chart: `1.14.0`
- IAM policy source: `https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.14.1/docs/install/iam_policy.json`

Other add-on versions:

- Metrics Server Helm chart: `3.13.0`
- kube-prometheus-stack Helm chart: `86.1.0`
- Amazon CloudWatch Observability EKS add-on: use the default version selected by EKS for the cluster version

## 1. Connect To EKS

```bash
AWS_REGION="$(terraform -chdir=infra output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"
```

Verify:

```bash
kubectl get nodes -o wide
```

Expected:

- At least one EKS worker node is `Ready`
- Node instance type matches the Terraform node group settings

## 2. AWS Load Balancer Controller

Terraform creates the IAM policy and IRSA role for this controller:

```bash
terraform -chdir=infra output -raw aws_load_balancer_controller_role_arn
```

Install with Helm:

```bash
AWS_REGION="$(terraform -chdir=infra output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"
VPC_ID="$(terraform -chdir=infra output -raw vpc_id)"
ALB_ROLE_ARN="$(terraform -chdir=infra output -raw aws_load_balancer_controller_role_arn)"
ALB_CHART_VERSION="$(terraform -chdir=infra output -raw aws_load_balancer_controller_chart_version)"

helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set region="$AWS_REGION" \
  --set vpcId="$VPC_ID" \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="$ALB_ROLE_ARN" \
  --version "$ALB_CHART_VERSION"
```

Verify:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

Expected:

- Deployment shows `READY 2/2`
- Controller pods are `Running`

## 3. Metrics Server

Metrics Server is required for CPU-based HPA metrics.

Install:

```bash
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update metrics-server

helm upgrade --install metrics-server metrics-server/metrics-server \
  --namespace kube-system \
  --version 3.13.0
```

Verify:

```bash
kubectl get deployment -n kube-system metrics-server
kubectl top nodes
kubectl top pods -A
```

Expected:

- Metrics Server deployment is available
- `kubectl top nodes` returns CPU and memory values

## 4. CloudWatch Observability

The Terraform node IAM role already includes `CloudWatchAgentServerPolicy`, so the short demo can use the worker-node IAM permission path documented by AWS.

Install the EKS add-on:

```bash
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"

aws eks create-addon \
  --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-cloudwatch-observability
```

Verify:

```bash
aws eks describe-addon \
  --cluster-name "$CLUSTER_NAME" \
  --addon-name amazon-cloudwatch-observability \
  --query "addon.status" \
  --output text

kubectl get pods -n amazon-cloudwatch
```

Expected:

- Add-on status becomes `ACTIVE`
- CloudWatch Agent and Fluent Bit pods are `Running`

Verify log groups after the app is deployed:

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/containerinsights/${CLUSTER_NAME}" \
  --query "logGroups[].logGroupName" \
  --output table
```

Expected:

- `/aws/containerinsights/<cluster-name>/application`
- `/aws/containerinsights/<cluster-name>/dataplane`
- `/aws/containerinsights/<cluster-name>/host`

## 5. Prometheus And Grafana

Install kube-prometheus-stack in a dedicated namespace:

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
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Expected:

- Prometheus Operator pods are `Running`
- Grafana pod is `Running`
- Prometheus pod is `Running`

Access Grafana locally:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Open:

```text
http://localhost:3000
```

Get Grafana admin password:

```bash
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

## 6. Deploy CloudOps App With Helm

After ECR images are pushed and the database secret exists:

```bash
kubectl create namespace cloudops --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install cloudops charts/cloudops-sre-platform \
  --namespace cloudops \
  -f charts/cloudops-sre-platform/values-aws-example.yaml \
  --set backend.image.repository="$(terraform -chdir=infra output -raw backend_ecr_repository_url)" \
  --set frontend.image.repository="$(terraform -chdir=infra output -raw frontend_ecr_repository_url)"
```

Verify:

```bash
kubectl get pods,svc,ingress,hpa -n cloudops -o wide
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-frontend -n cloudops
```

## 7. Evidence To Capture

Capture screenshots of:

- `kubectl get nodes -o wide`
- `kubectl get deployment -n kube-system aws-load-balancer-controller`
- `kubectl top nodes`
- `aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name amazon-cloudwatch-observability`
- CloudWatch application log group with backend/frontend pod logs
- `kubectl get pods -n monitoring`
- Grafana dashboard showing pod CPU/memory
- `kubectl get pods,svc,ingress,hpa -n cloudops -o wide`
- Live CloudOps dashboard on the ALB URL

## 8. Cleanup Reminder

Before running `terraform destroy`, delete Helm releases that created load balancers or persistent Kubernetes resources:

```bash
helm uninstall cloudops -n cloudops
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall metrics-server -n kube-system
helm uninstall aws-load-balancer-controller -n kube-system

aws eks delete-addon \
  --cluster-name "$(terraform -chdir=infra output -raw cluster_name)" \
  --addon-name amazon-cloudwatch-observability
```

Then run:

```bash
terraform -chdir=infra destroy
```
