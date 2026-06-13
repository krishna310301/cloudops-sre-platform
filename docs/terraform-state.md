# Terraform State

CloudOps SRE Platform is designed to support two Terraform state modes:

- **Local state for the short-lived AWS run**
- **Remote S3 state for repeatable team-style deployments**

The completed AWS demo used the local-first workflow because the environment was created, documented, and destroyed the same day. Local state is acceptable for that single-operator demo path as long as state files are never committed.

Remote state is the better pattern when more than one person or machine might run Terraform, or when the environment is expected to live beyond a short demo window.

## Local Demo State

The default repository workflow does not enable a backend:

```bash
terraform -chdir=infra init -backend=false
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
```

For a short-lived AWS demo, run normal Terraform initialization from `infra/` without copying a backend file:

```bash
terraform -chdir=infra init
terraform -chdir=infra plan
terraform -chdir=infra apply
```

State files are ignored by git:

```text
*.tfstate
*.tfstate.*
```

Keep local state private because it can contain resource identifiers and sensitive metadata.

## Optional Remote S3 State

Use remote state when you want a more production-style workflow:

- Shared state across machines
- S3 versioning for state recovery
- Server-side encryption
- Public access blocked
- State locking through the S3 backend lock file

The template lives at:

```text
infra/backend.tf.example
```

Copy it only when you are ready to use remote state:

```bash
cp infra/backend.tf.example infra/backend.tf
```

Edit these values:

```hcl
bucket = "REPLACE_WITH_UNIQUE_TFSTATE_BUCKET"
key    = "cloudops-sre-platform/demo/terraform.tfstate"
region = "us-east-1"
```

Then initialize and migrate local state if you already applied resources:

```bash
terraform -chdir=infra init -migrate-state
```

If no local state exists and you are only switching backend configuration:

```bash
terraform -chdir=infra init -reconfigure
```

## Backend Bootstrap Notes

Create the state bucket outside this application stack. Do not use the same Terraform configuration to create the bucket that stores its own state.

Recommended S3 bucket settings:

- Block all public access
- Enable bucket versioning
- Enable server-side encryption
- Restrict access to the deployment role or operator identity
- Allow S3 lock-file read/write/delete permissions for the `.tflock` object

The example uses:

```hcl
use_lockfile = true
```

That keeps the demo documentation aligned with Terraform's current S3 backend locking path without requiring a DynamoDB table.

## Cleanup Notes

Remote state changes the cleanup order:

1. Destroy CloudOps application infrastructure with `terraform destroy`.
2. Confirm EKS, RDS, ALB, NAT Gateway, and worker nodes are gone.
3. Keep the state bucket if you plan to reuse the backend.
4. Delete the state bucket only after confirming no Terraform-managed resources remain.

Do not delete the remote state bucket before `terraform destroy`; Terraform needs state to know what to remove.
