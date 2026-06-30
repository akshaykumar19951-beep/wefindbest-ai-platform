from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RequestLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    method: str
    path: str
    status_code: int
    latency_ms: int
    user_id: int | None
    api_key_prefix: str | None
    ip_address: str | None
    user_agent: str | None
    error: str | None
    created_at: datetime | None


class ErrorEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_log_id: int | None
    user_id: int | None
    method: str | None
    path: str | None
    status_code: int | None
    error_type: str
    message: str
    created_at: datetime | None


class UserActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: str | None
    created_at: datetime | None


class ProviderMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    provider: str
    model: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    success: bool
    error: str | None
    created_at: datetime | None


class AlertCreateRequest(BaseModel):
    severity: str = Field(default="info", pattern="^(info|warning|critical)$")
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)
    source: str = Field(default="system", min_length=1, max_length=80)


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    severity: str
    title: str
    message: str
    source: str
    status: str
    created_at: datetime | None
    resolved_at: datetime | None


class ObservabilitySummary(BaseModel):
    request_count: int
    error_count: int
    average_api_latency_ms: float
    average_provider_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    open_alerts: int
    health_status: str


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    providers_healthy: int
    providers_total: int
    open_alerts: int
    recent_errors: int
