from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_jwt_user, require_roles
from app.core.deps import get_db
from app.db.models import Alert, ErrorEvent, ProviderMetric, RequestLog, User, UserActivity
from app.schemas.observability import (
    AlertCreateRequest,
    AlertResponse,
    ErrorEventResponse,
    ObservabilitySummary,
    ProviderMetricResponse,
    RequestLogResponse,
    SystemHealthResponse,
    UserActivityResponse,
)
from app.services.observability_service import (
    acknowledge_alert,
    create_alert,
    observability_summary,
    provider_latency_by_name,
    record_user_activity,
    resolve_alert,
    system_health,
)

router = APIRouter()


@router.get("/summary", response_model=ObservabilitySummary)
def summary(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return observability_summary(db)


@router.get("/requests", response_model=list[RequestLogResponse])
def request_logs(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db), limit: int = 50):
    limit = min(max(limit, 1), 200)
    return db.query(RequestLog).order_by(RequestLog.created_at.desc()).limit(limit).all()


@router.get("/errors", response_model=list[ErrorEventResponse])
def error_events(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db), limit: int = 50):
    limit = min(max(limit, 1), 200)
    return db.query(ErrorEvent).order_by(ErrorEvent.created_at.desc()).limit(limit).all()


@router.get("/activity", response_model=list[UserActivityResponse])
def user_activity(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db), limit: int = 50):
    limit = min(max(limit, 1), 200)
    return db.query(UserActivity).order_by(UserActivity.created_at.desc()).limit(limit).all()


@router.get("/providers", response_model=list[ProviderMetricResponse])
def provider_metrics(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db), limit: int = 50):
    limit = min(max(limit, 1), 200)
    return db.query(ProviderMetric).order_by(ProviderMetric.created_at.desc()).limit(limit).all()


@router.get("/providers/latency")
def provider_latency(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return provider_latency_by_name(db)


@router.get("/alerts", response_model=list[AlertResponse])
def alerts(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


@router.post("/alerts", response_model=AlertResponse)
def create_alert_route(
    payload: AlertCreateRequest,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    alert = create_alert(
        db,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        source=payload.source,
    )
    record_user_activity(
        db,
        user_id=admin.id,
        action="alert.created",
        resource_type="alert",
        details=payload.title,
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert_route(
    alert_id: int,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    acknowledge_alert(db, alert)
    record_user_activity(db, user_id=admin.id, action="alert.acknowledged", resource_type="alert", resource_id=str(alert.id))
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert_route(
    alert_id: int,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    resolve_alert(db, alert)
    record_user_activity(db, user_id=admin.id, action="alert.resolved", resource_type="alert", resource_id=str(alert.id))
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/system-health", response_model=SystemHealthResponse)
def system_health_route(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return system_health(db)
