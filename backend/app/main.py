from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import SessionLocal, get_db, init_db
from app.models import Deployment, Incident, IncidentUpdate, Service
from app.schemas import (
    DeploymentCreate,
    DeploymentRead,
    IncidentCreate,
    IncidentDetail,
    IncidentRead,
    IncidentResolve,
    IncidentTimelineCreate,
    MetricsRead,
    ServiceCreate,
    ServiceRead,
    ServiceStatusUpdate,
    ServiceUpdate,
)
from app.seed import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="CloudOps SRE Platform API",
    description="Reliability operations API for services, incidents, deployments, and SLO metrics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def calculate_mttr_minutes(incident: Incident) -> float | None:
    if not incident.resolved_at:
        return None
    started_at = incident.started_at
    resolved_at = incident.resolved_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=timezone.utc)
    return round((resolved_at - started_at).total_seconds() / 60, 2)


def incident_to_read(incident: Incident) -> IncidentRead:
    return IncidentRead.model_validate(incident).model_copy(
        update={"mttr_minutes": calculate_mttr_minutes(incident)}
    )


def get_service_or_404(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


def get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.scalar(
        select(Incident)
        .options(selectinload(Incident.updates))
        .where(Incident.id == incident_id)
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/demo/cpu")
def cpu_load_demo(
    duration_ms: int = Query(default=250, ge=10, le=2000),
) -> dict[str, int | str]:
    """Bounded CPU work used only to demonstrate Kubernetes HPA scale-out."""
    started = perf_counter()
    deadline = started + (duration_ms / 1000)
    checksum = 0
    iterations = 0

    while perf_counter() < deadline:
        iterations += 1
        checksum = (checksum + (iterations * iterations)) % 1_000_003

    elapsed_ms = int((perf_counter() - started) * 1000)
    return {
        "status": "ok",
        "purpose": "hpa-demo",
        "requested_ms": duration_ms,
        "elapsed_ms": elapsed_ms,
        "iterations": iterations,
        "checksum": checksum,
    }


@app.get("/services", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)) -> list[Service]:
    return list(db.scalars(select(Service).order_by(Service.name)))


@app.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)) -> Service:
    service = Service(**payload.model_dump(mode="json"))
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@app.patch("/services/{service_id}", response_model=ServiceRead)
def update_service(
    service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)
) -> Service:
    service = get_service_or_404(db, service_id)
    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@app.patch("/services/{service_id}/status", response_model=ServiceRead)
def update_service_status(
    service_id: int, payload: ServiceStatusUpdate, db: Session = Depends(get_db)
) -> Service:
    service = get_service_or_404(db, service_id)
    service.status = payload.status
    db.commit()
    db.refresh(service)
    return service


@app.get("/incidents", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db)) -> list[IncidentRead]:
    incidents = db.scalars(select(Incident).order_by(Incident.created_at.desc())).all()
    return [incident_to_read(incident) for incident in incidents]


@app.post("/incidents", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    get_service_or_404(db, payload.service_id)
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.flush()
    db.add(
        IncidentUpdate(
            incident_id=incident.id,
            message=f"Incident opened with severity {incident.severity}.",
            status=incident.status,
        )
    )
    db.commit()
    db.refresh(incident)
    return incident_to_read(incident)


@app.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentDetail:
    incident = get_incident_or_404(db, incident_id)
    return IncidentDetail.model_validate(incident).model_copy(
        update={"mttr_minutes": calculate_mttr_minutes(incident)}
    )


@app.post(
    "/incidents/{incident_id}/updates",
    response_model=IncidentDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_incident_update(
    incident_id: int, payload: IncidentTimelineCreate, db: Session = Depends(get_db)
) -> IncidentDetail:
    incident = get_incident_or_404(db, incident_id)
    incident.status = payload.status
    db.add(
        IncidentUpdate(
            incident_id=incident.id,
            message=payload.message,
            status=payload.status,
        )
    )
    db.commit()
    return get_incident(incident_id, db)


@app.patch("/incidents/{incident_id}/resolve", response_model=IncidentDetail)
def resolve_incident(
    incident_id: int, payload: IncidentResolve, db: Session = Depends(get_db)
) -> IncidentDetail:
    incident = get_incident_or_404(db, incident_id)
    incident.status = "resolved"
    incident.resolved_at = datetime.now(timezone.utc)
    db.add(
        IncidentUpdate(
            incident_id=incident.id,
            message=payload.message,
            status="resolved",
        )
    )
    db.commit()
    return get_incident(incident_id, db)


@app.get("/deployments", response_model=list[DeploymentRead])
def list_deployments(db: Session = Depends(get_db)) -> list[Deployment]:
    return list(db.scalars(select(Deployment).order_by(Deployment.deployed_at.desc())))


@app.post("/deployments", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def create_deployment(payload: DeploymentCreate, db: Session = Depends(get_db)) -> Deployment:
    get_service_or_404(db, payload.service_id)
    values = payload.model_dump(exclude_none=True)
    deployment = Deployment(**values)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


@app.get("/metrics", response_model=MetricsRead)
def get_metrics(db: Session = Depends(get_db)) -> MetricsRead:
    services = db.scalars(select(Service)).all()
    incidents = db.scalars(select(Incident)).all()
    deployments = db.scalars(select(Deployment).order_by(Deployment.deployed_at.desc())).all()

    resolved_durations = [
        (incident.resolved_at - incident.started_at).total_seconds() / 60
        for incident in incidents
        if incident.resolved_at
    ]
    open_incidents = [incident for incident in incidents if incident.status != "resolved"]
    open_by_severity = {severity: 0 for severity in ["P1", "P2", "P3", "P4"]}
    for incident in open_incidents:
        open_by_severity[incident.severity] += 1

    degraded_down_services = [
        service for service in services if service.status in {"degraded", "down"}
    ]
    critical = any(incident.severity == "P1" for incident in open_incidents) or any(
        service.status == "down" for service in services
    )
    platform_status = "critical" if critical else "degraded" if open_incidents or degraded_down_services else "operational"

    failed_deployments = db.scalar(
        select(func.count()).select_from(Deployment).where(Deployment.status == "failed")
    )

    return MetricsRead(
        total_services=len(services),
        healthy_services=len([service for service in services if service.status == "healthy"]),
        degraded_down_services=len(degraded_down_services),
        open_incidents=len(open_incidents),
        average_mttr_minutes=round(sum(resolved_durations) / len(resolved_durations), 2)
        if resolved_durations
        else None,
        failed_deployments=failed_deployments or 0,
        last_deployment=deployments[0] if deployments else None,
        current_platform_status=platform_status,
        open_incidents_by_severity=open_by_severity,
    )
