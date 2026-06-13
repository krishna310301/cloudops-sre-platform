# RDS Connectivity And Secret Rotation Runbook

Use this runbook when backend pods cannot connect to Amazon RDS PostgreSQL, the
database secret is wrong or stale, or a demo needs database credential rotation.

## Symptoms

- Backend pods are `CrashLoopBackOff` or fail readiness checks.
- `/api/health` works intermittently or `/api/metrics` fails.
- Backend logs show connection refused, timeout, authentication failed, DNS, or
  SQLAlchemy/psycopg connection pool errors.
- The Helm migration Job fails before backend pods roll out.
- CloudOps UI loads but service, incident, deployment, or metrics data is empty
  because API calls fail.

## Initial Kubernetes Checks

```bash
kubectl get pods,job,svc,ingress,hpa -n cloudops -o wide
kubectl get events -n cloudops --sort-by=.lastTimestamp
kubectl describe pod -n cloudops -l app.kubernetes.io/component=backend
kubectl logs -n cloudops deploy/cloudops-cloudops-sre-platform-backend --tail=100
kubectl logs -n cloudops job/cloudops-cloudops-sre-platform-backend-migrate --tail=100
```

Confirm the application secret exists and contains the expected key:

```bash
kubectl get secret cloudops-database -n cloudops
kubectl get secret cloudops-database -n cloudops \
  -o jsonpath='{.data.database_url}' | base64 --decode
```

Do not paste decoded credentials into tickets, screenshots, or public notes.

## RDS And Secrets Manager Checks

```bash
AWS_REGION="$(terraform -chdir=infra output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir=infra output -raw cluster_name)"
RDS_ENDPOINT="$(terraform -chdir=infra output -raw rds_endpoint)"
SECRET_ARN="$(terraform -chdir=infra output -raw database_secret_arn)"
```

Check RDS status:

```bash
aws rds describe-db-instances \
  --region "$AWS_REGION" \
  --db-instance-identifier "${CLUSTER_NAME}-postgres" \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Port:Endpoint.Port,Public:PubliclyAccessible,SGs:VpcSecurityGroups[*].VpcSecurityGroupId}' \
  --output table
```

Check the Secrets Manager payload shape:

```bash
aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ARN" \
  --query SecretString \
  --output text | jq '{username, host, port, dbname, has_database_url: has("database_url")}'
```

Expected:

- RDS status is `available`.
- `Public` is `false`.
- Secret contains `username`, `host`, `port`, `dbname`, and `database_url`.
- Secret `host` matches the Terraform `rds_endpoint` output.

## Security Group Validation

```bash
RDS_SG_ID="$(aws rds describe-db-instances \
  --region "$AWS_REGION" \
  --db-instance-identifier "${CLUSTER_NAME}-postgres" \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)"

EKS_CLUSTER_SG_ID="$(aws eks describe-cluster \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME" \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' \
  --output text)"

aws ec2 describe-security-groups \
  --region "$AWS_REGION" \
  --group-ids "$RDS_SG_ID" \
  --query 'SecurityGroups[0].IpPermissions' \
  --output json
```

Expected:

- TCP `5432` is allowed from `$EKS_CLUSTER_SG_ID`.
- RDS is not open to `0.0.0.0/0`.
- RDS subnets are database/private subnets, not public subnets.

## Connectivity Test From The Cluster

```bash
DATABASE_URL="$(kubectl get secret cloudops-database -n cloudops \
  -o jsonpath='{.data.database_url}' | base64 --decode)"

kubectl run rds-connectivity-check \
  -n cloudops \
  --rm -it \
  --restart=Never \
  --image=postgres:16-alpine \
  --env="DATABASE_URL=${DATABASE_URL}" \
  --command -- sh -lc 'psql "$DATABASE_URL" -c "select now();"'
```

If this fails:

- Timeout usually points to subnet, route, security group, or DNS issues.
- Authentication failure points to a stale Kubernetes Secret or rotated RDS
  password not synced into the cluster.
- Database-not-found points to `db_name` or connection string mismatch.

## Secret Rotation Steps

This project stores the generated database URL in Secrets Manager, then the
deployment workflow syncs it into the `cloudops-database` Kubernetes Secret.

For a short demo, rotate by replacing the RDS master password and updating the
Secrets Manager JSON payload:

```bash
NEW_PASSWORD="$(openssl rand -base64 24 | tr -d '=+/' | cut -c1-24)"

aws rds modify-db-instance \
  --region "$AWS_REGION" \
  --db-instance-identifier "${CLUSTER_NAME}-postgres" \
  --master-user-password "$NEW_PASSWORD" \
  --apply-immediately

aws rds wait db-instance-available \
  --region "$AWS_REGION" \
  --db-instance-identifier "${CLUSTER_NAME}-postgres"
```

Update Secrets Manager:

```bash
SECRET_JSON="$(aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ARN" \
  --query SecretString \
  --output text)"

UPDATED_SECRET_JSON="$(echo "$SECRET_JSON" | jq \
  --arg password "$NEW_PASSWORD" \
  --arg host "$RDS_ENDPOINT" \
  '.password = $password |
   .host = $host |
   .database_url = "postgresql+psycopg://\(.username):\($password)@\(.host):\(.port)/\(.dbname)"')"

aws secretsmanager put-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ARN" \
  --secret-string "$UPDATED_SECRET_JSON"
```

Sync the Kubernetes Secret and restart backend pods:

```bash
DATABASE_URL="$(echo "$UPDATED_SECRET_JSON" | jq -r '.database_url')"

kubectl create secret generic cloudops-database \
  --namespace cloudops \
  --from-literal=database_url="$DATABASE_URL" \
  --dry-run=client \
  -o yaml | kubectl apply -f -

kubectl rollout restart deployment/cloudops-cloudops-sre-platform-backend -n cloudops
kubectl rollout status deployment/cloudops-cloudops-sre-platform-backend -n cloudops --timeout=180s
```

Run the connectivity test again and verify the API:

```bash
curl "$ALB_URL/api/health"
curl "$ALB_URL/api/metrics"
```

## Rollback

If rotation fails:

1. Restore the previous Secrets Manager JSON payload with
   `aws secretsmanager put-secret-value`.
2. Recreate the Kubernetes `cloudops-database` Secret from the restored
   `database_url`.
3. Restart the backend deployment.
4. Run the connectivity test and API smoke checks.
5. Add an incident timeline update in the CloudOps UI with the failed rotation
   cause and rollback time.

If the Helm migration Job failed during deployment, fix or restore the secret,
then rerun:

```bash
helm upgrade --install cloudops charts/cloudops-sre-platform \
  --namespace cloudops \
  -f charts/cloudops-sre-platform/values-aws-example.yaml
```

## Demo Evidence To Capture

- Backend pod status before and after the fix.
- Backend logs showing database connection errors and later recovery.
- RDS instance status and private endpoint.
- RDS security group inbound rule for PostgreSQL from the EKS cluster security
  group.
- Secrets Manager payload shape with credential values redacted.
- Kubernetes Secret recreation command output, with credentials redacted.
- `kubectl rollout status` after backend restart.
- `/api/health` and `/api/metrics` after recovery.
- CloudOps incident timeline showing investigation, mitigation, and resolution.
