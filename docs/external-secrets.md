# Optional External Secrets Sync

The default AWS deployment keeps secrets simple: GitHub Actions reads the Terraform-created AWS Secrets Manager value and writes a Kubernetes Secret named `cloudops-database` before Helm deploys the app.

For a more production-style path, the Helm chart can instead render an External Secrets Operator `ExternalSecret` that syncs the same AWS Secrets Manager value into the Kubernetes Secret used by the backend and migration Job.

This option is off by default. Local development and Docker Compose are unchanged.

## Prerequisites

- External Secrets Operator is installed in the EKS cluster
- The cluster has an IAM/OIDC path that lets the External Secrets controller read the database secret from AWS Secrets Manager
- The database secret contains a `database_url` property
- The CloudOps backend keeps using the Kubernetes Secret name `cloudops-database`

Terraform already creates the EKS OIDC provider used by IRSA patterns. If using IRSA for External Secrets, create an IAM role for the External Secrets controller service account with read access to the database secret.

Minimum AWS permission shape:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:cloudops-sre-platform-demo/database-*"
    }
  ]
}
```

## Install External Secrets Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update external-secrets

helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace
```

Verify:

```bash
kubectl get pods -n external-secrets
kubectl get crd | grep external-secrets
```

## Create A Secret Store

For an IRSA-backed controller, create a `ClusterSecretStore` like this:

```yaml
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secretsmanager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

Apply it:

```bash
kubectl apply -f cluster-secret-store.yaml
kubectl get clustersecretstore aws-secretsmanager
```

## Enable The Helm Option

Create an override file for the AWS run:

```yaml
backend:
  database:
    existingSecret: cloudops-database
    secretKey: database_url
    createSecret: false
    externalSecret:
      enabled: true
      secretStoreRef:
        name: aws-secretsmanager
        kind: ClusterSecretStore
      remoteSecretName: cloudops-sre-platform-demo/database
      remoteProperty: database_url
```

Deploy:

```bash
helm upgrade --install cloudops charts/cloudops-sre-platform \
  --namespace cloudops \
  -f charts/cloudops-sre-platform/values-aws-example.yaml \
  -f values-external-secrets.yaml \
  --set backend.image.repository="$(terraform -chdir=infra output -raw backend_ecr_repository_url)" \
  --set frontend.image.repository="$(terraform -chdir=infra output -raw frontend_ecr_repository_url)" \
  --set backend.image.tag="$IMAGE_TAG" \
  --set frontend.image.tag="$IMAGE_TAG"
```

## Verify

```bash
kubectl get externalsecret -n cloudops
kubectl describe externalsecret -n cloudops cloudops-cloudops-sre-platform-database
kubectl get secret -n cloudops cloudops-database
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops
```

Expected:

- `ExternalSecret` reports synced/ready
- Kubernetes Secret `cloudops-database` exists
- Backend and migration Job read the same `database_url` key

## Rollback To Manual Secret Sync

Disable the ExternalSecret override and return to the default GitHub Actions secret sync path:

```bash
helm upgrade --install cloudops charts/cloudops-sre-platform \
  --namespace cloudops \
  -f charts/cloudops-sre-platform/values-aws-example.yaml \
  --set backend.database.externalSecret.enabled=false
```

If needed, delete the generated `ExternalSecret`:

```bash
kubectl delete externalsecret -n cloudops cloudops-cloudops-sre-platform-database
```
