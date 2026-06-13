import logging
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

test_db = Path(f"/tmp/cloudops_sre_platform_test_{os.getpid()}.db")
if test_db.exists():
    test_db.unlink()

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{test_db}"
os.environ["CORS_ORIGINS"] = "http://testserver"

from app.main import app  # noqa: E402


def test_request_id_header_is_generated_when_missing():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_request_id_header_is_echoed_and_logged(caplog):
    request_id = "test-request-123"

    with TestClient(app) as client:
        with caplog.at_level(logging.INFO):
            response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id

    request_logs = [
        record for record in caplog.records if record.getMessage() == "request completed"
    ]
    assert any(
        record.request_id == request_id
        and record.http["method"] == "GET"
        and record.http["path"] == "/health"
        and record.http["status_code"] == 200
        for record in request_logs
    )


def test_incident_event_logs_include_request_and_resource_context(caplog):
    request_id = "incident-log-test-123"

    with TestClient(app) as client:
        service_id = client.get("/services").json()[0]["id"]

        with caplog.at_level(logging.INFO):
            incident_response = client.post(
                "/incidents",
                headers={"X-Request-ID": request_id},
                json={
                    "service_id": service_id,
                    "title": "Synthetic API latency above SLO",
                    "severity": "P2",
                    "status": "investigating",
                },
            )
            incident = incident_response.json()
            client.patch(
                f"/incidents/{incident['id']}/resolve",
                json={"message": "Resolved synthetic logging test incident."},
            )

    assert incident_response.status_code == 201

    incident_logs = [
        record for record in caplog.records if record.getMessage() == "incident created"
    ]
    assert any(
        record.request_id == request_id
        and record.event == "incident.created"
        and record.incident_id == incident["id"]
        and record.service_id == service_id
        and record.severity == "P2"
        for record in incident_logs
    )


def test_deployment_event_logs_include_request_and_resource_context(caplog):
    request_id = "deployment-log-test-123"

    with TestClient(app) as client:
        service_id = client.get("/services").json()[0]["id"]

        with caplog.at_level(logging.INFO):
            deployment_response = client.post(
                "/deployments",
                headers={"X-Request-ID": request_id},
                json={
                    "service_id": service_id,
                    "version": "v8.8.8-log-test",
                    "commit_sha": "def5678",
                    "status": "success",
                },
            )

    assert deployment_response.status_code == 201
    deployment = deployment_response.json()

    deployment_logs = [
        record for record in caplog.records if record.getMessage() == "deployment registered"
    ]
    assert any(
        record.request_id == request_id
        and record.event == "deployment.registered"
        and record.deployment_id == deployment["id"]
        and record.service_id == service_id
        and record.deployment_status == "success"
        and record.commit_sha == "def5678"
        for record in deployment_logs
    )


def test_health_and_seeded_metrics():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "environment": "test"}

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        payload = metrics.json()
        assert payload["total_services"] == 3
        assert payload["open_incidents"] == 1
        assert payload["failed_deployments"] == 1
        assert payload["current_platform_status"] == "critical"
        assert payload["services_meeting_slo"] == 2
        assert payload["services_breaching_slo"] == 1
        assert payload["average_sli_uptime_percent"] == 66.67
        checkout_reliability = next(
            item for item in payload["service_reliability"] if item["name"] == "checkout-web"
        )
        assert checkout_reliability["slo_target"] == 99.9
        assert checkout_reliability["sli_uptime_percent"] == 0.0
        assert checkout_reliability["error_budget_status"] == "exhausted"


def test_bounded_cpu_demo_endpoint():
    with TestClient(app) as client:
        response = client.get("/demo/cpu?duration_ms=10")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["purpose"] == "hpa-demo"
        assert payload["requested_ms"] == 10
        assert payload["iterations"] > 0


def test_service_create_and_status_update():
    with TestClient(app) as client:
        response = client.post(
            "/services",
            json={
                "name": "orders-api-test",
                "owner": "Platform SRE",
                "environment": "staging",
                "status": "healthy",
                "slo_target": 99.9,
                "service_url": "https://orders.internal.example.com",
                "current_version": "v1.0.0",
            },
        )
        assert response.status_code == 201
        service = response.json()
        assert service["name"] == "orders-api-test"

        status_response = client.patch(
            f"/services/{service['id']}/status",
            json={"status": "degraded"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "degraded"


def test_incident_timeline_and_resolution():
    with TestClient(app) as client:
        service_id = client.get("/services").json()[0]["id"]

        incident_response = client.post(
            "/incidents",
            json={
                "service_id": service_id,
                "title": "Synthetic health check failures",
                "severity": "P2",
                "status": "investigating",
            },
        )
        assert incident_response.status_code == 201
        incident = incident_response.json()

        update_response = client.post(
            f"/incidents/{incident['id']}/updates",
            json={
                "message": "Identified failing readiness probe after deployment.",
                "status": "identified",
            },
        )
        assert update_response.status_code == 201
        assert update_response.json()["status"] == "identified"
        assert len(update_response.json()["updates"]) == 2

        resolve_response = client.patch(
            f"/incidents/{incident['id']}/resolve",
            json={"message": "Rolled back deployment and service recovered."},
        )
        assert resolve_response.status_code == 200
        resolved = resolve_response.json()
        assert resolved["status"] == "resolved"
        assert resolved["resolved_at"] is not None
        assert resolved["mttr_minutes"] is not None


def test_deployment_registration():
    with TestClient(app) as client:
        service_id = client.get("/services").json()[0]["id"]

        response = client.post(
            "/deployments",
            json={
                "service_id": service_id,
                "version": "v9.9.9-test",
                "commit_sha": "abc1234",
                "status": "success",
            },
        )
        assert response.status_code == 201
        deployment = response.json()
        assert deployment["version"] == "v9.9.9-test"
        assert deployment["commit_sha"] == "abc1234"

        deployments = client.get("/deployments").json()
        assert any(item["version"] == "v9.9.9-test" for item in deployments)
