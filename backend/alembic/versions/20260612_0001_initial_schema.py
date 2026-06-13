"""Initial CloudOps schema.

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12 23:10:00 UTC
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260612_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("slo_target", sa.Float(), nullable=False),
        sa.Column("service_url", sa.String(length=255), nullable=True),
        sa.Column("current_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)
    op.create_index(op.f("ix_services_name"), "services", ["name"], unique=True)

    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deployments_id"), "deployments", ["id"], unique=False)
    op.create_index(op.f("ix_deployments_service_id"), "deployments", ["service_id"], unique=False)

    op.create_table(
        "health_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_health_checks_id"), "health_checks", ["id"], unique=False)
    op.create_index(op.f("ix_health_checks_service_id"), "health_checks", ["service_id"], unique=False)

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incidents_id"), "incidents", ["id"], unique=False)
    op.create_index(op.f("ix_incidents_service_id"), "incidents", ["service_id"], unique=False)

    op.create_table(
        "incident_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incident_updates_id"), "incident_updates", ["id"], unique=False)
    op.create_index(op.f("ix_incident_updates_incident_id"), "incident_updates", ["incident_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_updates_incident_id"), table_name="incident_updates")
    op.drop_index(op.f("ix_incident_updates_id"), table_name="incident_updates")
    op.drop_table("incident_updates")

    op.drop_index(op.f("ix_incidents_service_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_id"), table_name="incidents")
    op.drop_table("incidents")

    op.drop_index(op.f("ix_health_checks_service_id"), table_name="health_checks")
    op.drop_index(op.f("ix_health_checks_id"), table_name="health_checks")
    op.drop_table("health_checks")

    op.drop_index(op.f("ix_deployments_service_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_id"), table_name="deployments")
    op.drop_table("deployments")

    op.drop_index(op.f("ix_services_name"), table_name="services")
    op.drop_index(op.f("ix_services_id"), table_name="services")
    op.drop_table("services")
