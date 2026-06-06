from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Deployment, HealthCheck, Incident, IncidentUpdate, Service


def seed_database(db: Session) -> None:
    existing_service = db.scalar(select(Service).limit(1))
    if existing_service:
        return

    now = datetime.now(timezone.utc)

    api = Service(
        name="payments-api",
        owner="Platform SRE",
        environment="production",
        status="healthy",
        slo_target=99.95,
        service_url="https://payments.internal.example.com",
        current_version="v2.8.4",
    )
    checkout = Service(
        name="checkout-web",
        owner="Cloud Operations",
        environment="production",
        status="degraded",
        slo_target=99.9,
        service_url="https://checkout.internal.example.com",
        current_version="v1.14.2",
    )
    telemetry = Service(
        name="telemetry-worker",
        owner="Observability",
        environment="staging",
        status="healthy",
        slo_target=99.5,
        service_url=None,
        current_version="v0.9.7",
    )

    db.add_all([api, checkout, telemetry])
    db.flush()

    resolved = Incident(
        service_id=api.id,
        title="Elevated payment authorization latency",
        severity="P2",
        status="resolved",
        started_at=now - timedelta(hours=6),
        resolved_at=now - timedelta(hours=4, minutes=20),
    )
    active = Incident(
        service_id=checkout.id,
        title="Checkout error rate above SLO threshold",
        severity="P1",
        status="monitoring",
        started_at=now - timedelta(minutes=42),
    )
    db.add_all([resolved, active])
    db.flush()

    db.add_all(
        [
            IncidentUpdate(
                incident_id=resolved.id,
                message="CloudWatch alarm triggered for p95 latency above 900 ms.",
                status="investigating",
                created_at=now - timedelta(hours=6),
            ),
            IncidentUpdate(
                incident_id=resolved.id,
                message="RDS connection pool saturation identified after deployment.",
                status="identified",
                created_at=now - timedelta(hours=5, minutes=15),
            ),
            IncidentUpdate(
                incident_id=resolved.id,
                message="Rolled back API deployment and latency returned to baseline.",
                status="resolved",
                created_at=now - timedelta(hours=4, minutes=20),
            ),
            IncidentUpdate(
                incident_id=active.id,
                message="Synthetic checks detected intermittent 5xx responses.",
                status="investigating",
                created_at=now - timedelta(minutes=42),
            ),
            IncidentUpdate(
                incident_id=active.id,
                message="Traffic shifted away from one unhealthy backend pod.",
                status="monitoring",
                created_at=now - timedelta(minutes=15),
            ),
        ]
    )

    db.add_all(
        [
            Deployment(
                service_id=api.id,
                version="v2.8.4",
                commit_sha="9f3a2c1",
                status="success",
                deployed_at=now - timedelta(days=1, hours=3),
            ),
            Deployment(
                service_id=checkout.id,
                version="v1.14.2",
                commit_sha="e41c0aa",
                status="failed",
                deployed_at=now - timedelta(hours=1, minutes=10),
            ),
            Deployment(
                service_id=telemetry.id,
                version="v0.9.7",
                commit_sha="4bb91d8",
                status="success",
                deployed_at=now - timedelta(days=2),
            ),
        ]
    )

    db.add_all(
        [
            HealthCheck(service_id=api.id, status="healthy", latency_ms=84, checked_at=now),
            HealthCheck(service_id=checkout.id, status="degraded", latency_ms=710, checked_at=now),
            HealthCheck(service_id=telemetry.id, status="healthy", latency_ms=132, checked_at=now),
        ]
    )

    db.commit()
