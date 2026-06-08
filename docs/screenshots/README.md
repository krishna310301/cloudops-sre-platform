# Screenshots

Store sanitized AWS demo screenshots here after a short-lived deployment. These images can be used both as GitHub documentation and as source material for a LinkedIn project post.

Recommended folder pattern:

```text
docs/screenshots/aws-demo-YYYY-MM-DD/
```

Available galleries:

- [AWS demo screenshots - June 6, 2026](aws-demo-2026-06-06/)

Suggested file names are documented in:

```text
docs/evidence.md
```

Before committing screenshots:

- Crop or blur AWS account IDs, personal data, secrets, private endpoint details, and unnecessary browser chrome
- Keep each image focused on one validation point
- Prefer readable 16:9 screenshots for LinkedIn carousel reuse
- Avoid screenshots that show credentials, environment variables, database passwords, or full secret values

Recommended LinkedIn carousel order:

1. Live dashboard on ALB URL
2. EKS cluster and nodes
3. Kubernetes pods, services, ingress, and HPA
4. HPA scale-out during k6 load
5. GitHub Actions successful workflow
6. CloudWatch logs or Terraform destroy confirmation
