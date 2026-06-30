from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Alert, ErrorEvent, ProviderMetric, RequestLog, Usage, UserActivity
from app.services.ai_service import ai_service


def record_request_log(
    db: Session,
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    latency_ms: int,
    user_id: int | None = None,
    api_key_prefix: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    error: str | None = None,
) -> RequestLog:
    record = RequestLog(
        request_id=request_id,
        method=method,
        path=path,
        status_code=status_code,
        latency_ms=latency_ms,
        user_id=user_id,
        api_key_prefix=api_key_prefix,
        ip_address=ip_address,
        user_agent=user_agent,
        error=error,
    )
    db.add(record)
    return record


def record_error_event(
    db: Session,
    *,
    error_type: str,
    message: str,
    request_log_id: int | None = None,
    user_id: int | None = None,
    method: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    stack: str | None = None,
) -> ErrorEvent:
    event = ErrorEvent(
        request_log_id=request_log_id,
        user_id=user_id,
        method=method,
        path=path,
        status_code=status_code,
        error_type=error_type,
        message=message,
        stack=stack,
    )
    db.add(event)
    return event


def record_user_activity(
    db: Session,
    *,
    action: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: str | None = None,
) -> UserActivity:
    activity = UserActivity(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(activity)
    return activity


def record_provider_metric(
    db: Session,
    *,
    provider: str,
    model: str,
    latency_ms: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    cost_usd: float = 0.0,
    success: bool = True,
    user_id: int | None = None,
    error: str | None = None,
) -> ProviderMetric:
    metric = ProviderMetric(
        user_id=user_id,
        provider=provider,
        model=model,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        success=success,
        error=error,
    )
    db.add(metric)
    return metric


def create_alert(
    db: Session,
    *,
    severity: str,
    title: str,
    message: str,
    source: str = "system",
) -> Alert:
    alert = Alert(severity=severity, title=title, message=message, source=source)
    db.add(alert)
    return alert


def acknowledge_alert(db: Session, alert: Alert) -> Alert:
    alert.status = "acknowledged"
    return alert


def resolve_alert(db: Session, alert: Alert) -> Alert:
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    return alert


def observability_summary(db: Session) -> dict:
    request_count = db.query(RequestLog).count()
    error_count = db.query(ErrorEvent).count()
    avg_api_latency = db.query(func.avg(RequestLog.latency_ms)).scalar() or 0.0
    avg_provider_latency = db.query(func.avg(ProviderMetric.latency_ms)).scalar() or 0.0
    total_tokens = db.query(func.coalesce(func.sum(Usage.tokens), 0)).scalar() or 0
    total_cost = db.query(func.coalesce(func.sum(Usage.estimated_cost_usd), 0.0)).scalar() or 0.0
    open_alerts = db.query(Alert).filter(Alert.status != "resolved").count()

    if open_alerts or error_count:
        health_status = "degraded"
    else:
        health_status = "healthy"

    return {
        "request_count": request_count,
        "error_count": error_count,
        "average_api_latency_ms": round(float(avg_api_latency), 2),
        "average_provider_latency_ms": round(float(avg_provider_latency), 2),
        "total_tokens": int(total_tokens),
        "total_cost_usd": round(float(total_cost), 6),
        "open_alerts": open_alerts,
        "health_status": health_status,
    }


def system_health(db: Session) -> dict:
    providers = ai_service.health()
    recent_cutoff = datetime.utcnow() - timedelta(hours=1)
    recent_errors = db.query(ErrorEvent).filter(ErrorEvent.created_at >= recent_cutoff).count()
    open_alerts = db.query(Alert).filter(Alert.status != "resolved").count()
    healthy_count = len([provider for provider in providers if provider.healthy])
    status = "healthy"
    if recent_errors or open_alerts or healthy_count < len(providers):
        status = "degraded"

    return {
        "status": status,
        "database": "ok",
        "providers_healthy": healthy_count,
        "providers_total": len(providers),
        "open_alerts": open_alerts,
        "recent_errors": recent_errors,
    }


def provider_latency_by_name(db: Session) -> list[dict]:
    rows = (
        db.query(
            ProviderMetric.provider,
            func.count(ProviderMetric.id),
            func.avg(ProviderMetric.latency_ms),
            func.sum(ProviderMetric.total_tokens),
            func.sum(ProviderMetric.cost_usd),
        )
        .group_by(ProviderMetric.provider)
        .all()
    )
    return [
        {
            "provider": row[0],
            "requests": row[1],
            "average_latency_ms": round(float(row[2] or 0), 2),
            "total_tokens": int(row[3] or 0),
            "cost_usd": round(float(row[4] or 0), 6),
        }
        for row in rows
    ]
