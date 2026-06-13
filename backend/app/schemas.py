from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


ServiceStatus = Literal["healthy", "degraded", "down", "maintenance"]
IncidentSeverity = Literal["P1", "P2", "P3", "P4"]
IncidentStatus = Literal["investigating", "identified", "monitoring", "resolved"]
DeploymentStatus = Literal["success", "failed", "rolled_back", "in_progress"]


class ServiceBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    owner: str = Field(min_length=2, max_length=120)
    environment: str = Field(min_length=2, max_length=40)
    status: ServiceStatus = "healthy"
    slo_target: float = Field(default=99.9, ge=0, le=100)
    service_url: HttpUrl | None = None
    current_version: str = Field(default="v1.0.0", min_length=1, max_length=80)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    owner: str | None = Field(default=None, min_length=2, max_length=120)
    environment: str | None = Field(default=None, min_length=2, max_length=40)
    status: ServiceStatus | None = None
    slo_target: float | None = Field(default=None, ge=0, le=100)
    service_url: HttpUrl | None = None
    current_version: str | None = Field(default=None, min_length=1, max_length=80)


class ServiceStatusUpdate(BaseModel):
    status: ServiceStatus


class ServiceRead(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class IncidentUpdateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    message: str
    status: IncidentStatus
    created_at: datetime


class IncidentBase(BaseModel):
    service_id: int
    title: str = Field(min_length=3, max_length=160)
    severity: IncidentSeverity
    status: IncidentStatus = "investigating"


class IncidentCreate(IncidentBase):
    pass


class IncidentRead(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    mttr_minutes: float | None = None


class IncidentDetail(IncidentRead):
    updates: list[IncidentUpdateRead] = Field(default_factory=list)


class IncidentTimelineCreate(BaseModel):
    message: str = Field(min_length=3)
    status: IncidentStatus


class IncidentResolve(BaseModel):
    message: str = Field(default="Incident resolved and service restored.")


class DeploymentBase(BaseModel):
    service_id: int
    version: str = Field(min_length=1, max_length=80)
    commit_sha: str = Field(min_length=7, max_length=64)
    status: DeploymentStatus
    deployed_at: datetime | None = None


class DeploymentCreate(DeploymentBase):
    pass


class DeploymentRead(DeploymentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deployed_at: datetime
    created_at: datetime


class ServiceReliabilityRead(BaseModel):
    service_id: int
    name: str
    status: ServiceStatus
    slo_target: float
    sli_uptime_percent: float
    error_budget_percent: float
    error_budget_remaining_percent: float
    error_budget_burn_percent: float
    error_budget_status: Literal["healthy", "at_risk", "exhausted"]


class MetricsRead(BaseModel):
    total_services: int
    healthy_services: int
    degraded_down_services: int
    open_incidents: int
    average_mttr_minutes: float | None
    failed_deployments: int
    last_deployment: DeploymentRead | None
    current_platform_status: Literal["operational", "degraded", "critical"]
    open_incidents_by_severity: dict[str, int]
    services_meeting_slo: int
    services_breaching_slo: int
    average_sli_uptime_percent: float | None
    service_reliability: list[ServiceReliabilityRead]
