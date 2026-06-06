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
