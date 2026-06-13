from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra"


def read(name: str) -> str:
    return (INFRA / name).read_text()


def variable_default(source: str, name: str) -> str:
    match = re.search(
        rf'variable\s+"{re.escape(name)}"\s+\{{.*?default\s+=\s+(.+?)\n\}}',
        source,
        re.DOTALL,
    )
    if not match:
        raise AssertionError(f"Missing variable default for {name}")
    return match.group(1).strip().strip('"')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    variables = read("variables.tf")
    rds = read("rds.tf")
    vpc = read("vpc.tf")
    ecr = read("ecr.tf")
    cloudwatch = read("cloudwatch.tf")
    secrets = read("secrets.tf")

    require(variable_default(variables, "db_instance_class") == "db.t4g.micro", "RDS demo instance must stay db.t4g.micro")
    require(int(variable_default(variables, "db_allocated_storage_gb")) <= 20, "RDS allocated storage must stay <= 20 GB")
    require(int(variable_default(variables, "db_max_allocated_storage_gb")) <= 30, "RDS max storage must stay <= 30 GB")
    require(int(variable_default(variables, "node_desired_size")) <= 2, "EKS desired node count must stay <= 2")
    require(int(variable_default(variables, "node_max_size")) <= 4, "EKS max node count must stay <= 4")
    require(int(variable_default(variables, "cloudwatch_log_retention_days")) <= 7, "CloudWatch retention must stay <= 7 days")

    require('storage_encrypted     = true' in rds, "RDS storage encryption must remain enabled")
    require('publicly_accessible    = false' in rds, "RDS must not be publicly accessible")
    require('multi_az               = false' in rds, "RDS Multi-AZ must stay disabled for the short demo")
    require('backup_retention_period = 0' in rds, "RDS backup retention must stay disabled for same-day cleanup")
    require('deletion_protection     = false' in rds, "RDS deletion protection must stay disabled for same-day cleanup")
    require('skip_final_snapshot     = true' in rds, "RDS final snapshot must stay skipped for same-day cleanup")

    require('count = var.enable_nat_gateway ? 1 : 0' in vpc, "NAT Gateway count must stay capped at one")
    require("countNumber = 10" in ecr, "ECR lifecycle policy must keep image count capped")
    require("force_delete         = true" in ecr, "ECR repositories must stay force-deleteable for cleanup")
    require("retention_in_days = var.cloudwatch_log_retention_days" in cloudwatch, "CloudWatch logs must use bounded retention")
    require("recovery_window_in_days = 0" in secrets, "Secrets Manager recovery window must stay at 0 for cleanup")

    print("Terraform cost/security guardrails passed")


if __name__ == "__main__":
    main()
