from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_jwt_user, require_org_role, require_roles
from app.core.deps import get_db
from app.db.models import APIKey, AuditLog, LoginHistory, Organization, Session as UserSession, TeamMember, User
from app.schemas.auth import (
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyRotateRequest,
    AuditLogResponse,
    EmailVerificationRequest,
    LoginHistoryResponse,
    LoginRequest,
    LogoutRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    SessionResponse,
    TeamMemberInviteRequest,
    TeamMemberResponse,
    TokenResponse,
)
from app.services.auth_service import (
    audit,
    confirm_password_reset,
    create_api_key,
    login_user,
    refresh_session,
    register_user,
    request_password_reset,
    revoke_session,
    verify_email,
)

router = APIRouter()


def request_context(request: Request) -> tuple[str | None, str | None]:
    return request.client.host if request.client else None, request.headers.get("user-agent")


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ip_address, user_agent = request_context(request)
    return register_user(db, payload.email, payload.password, payload.organization_name, ip_address, user_agent)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip_address, user_agent = request_context(request)
    return login_user(db, payload.email, payload.password, ip_address, user_agent)


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_session(db, payload.refresh_token)


@router.post("/logout")
def logout(payload: LogoutRequest, user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    revoke_session(db, payload.refresh_token, actor_user_id=user.id)
    return {"status": "ok"}


@router.post("/verify-email")
def verify_email_route(payload: EmailVerificationRequest, db: Session = Depends(get_db)):
    verify_email(db, payload.token)
    return {"status": "verified"}


@router.post("/password-reset/request")
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    token = request_password_reset(db, payload.email)
    return {"status": "ok", "reset_token": token}


@router.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    confirm_password_reset(db, payload.token, payload.new_password)
    return {"status": "password_reset"}


@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(APIKey).filter(APIKey.user_id == user.id).order_by(APIKey.id.asc()).all()


@router.post("/api-keys", response_model=APIKeyResponse)
def create_key(payload: APIKeyCreateRequest, user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    key_record, raw_key = create_api_key(db, user, payload.name, payload.organization_id)
    audit(db, "api_key.created", user.id, payload.organization_id, "api_key", None)
    db.commit()
    db.refresh(key_record)
    response = APIKeyResponse.model_validate(key_record)
    response.key = raw_key
    return response


@router.post("/api-keys/{api_key_id}/rotate", response_model=APIKeyResponse)
def rotate_key(
    api_key_id: int,
    payload: APIKeyRotateRequest,
    user: User = Depends(get_current_jwt_user),
    db: Session = Depends(get_db),
):
    old_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user.id).first()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")
    old_key.is_active = False
    old_key.revoked_at = datetime.utcnow()
    new_key, raw_key = create_api_key(db, user, payload.name or old_key.name, old_key.organization_id)
    db.flush()
    new_key.rotated_from_id = old_key.id
    audit(db, "api_key.rotated", user.id, old_key.organization_id, "api_key", str(old_key.id))
    db.commit()
    db.refresh(new_key)
    response = APIKeyResponse.model_validate(new_key)
    response.key = raw_key
    return response


@router.delete("/api-keys/{api_key_id}")
def revoke_key(api_key_id: int, user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    key.revoked_at = datetime.utcnow()
    audit(db, "api_key.revoked", user.id, key.organization_id, "api_key", str(key.id))
    db.commit()
    return {"status": "revoked"}


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    payload: OrganizationCreateRequest,
    user: User = Depends(get_current_jwt_user),
    db: Session = Depends(get_db),
):
    org = Organization(name=payload.name, slug=payload.slug)
    db.add(org)
    db.flush()
    db.add(TeamMember(organization_id=org.id, user_id=user.id, role="owner"))
    audit(db, "organization.created", user.id, org.id, "organization", str(org.id))
    db.commit()
    db.refresh(org)
    return org


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return (
        db.query(Organization)
        .join(TeamMember)
        .filter(TeamMember.user_id == user.id)
        .order_by(Organization.id.asc())
        .all()
    )


@router.post("/organizations/{organization_id}/members", response_model=TeamMemberResponse)
def add_team_member(
    organization_id: int,
    payload: TeamMemberInviteRequest,
    user: User = Depends(get_current_jwt_user),
    db: Session = Depends(get_db),
):
    require_org_role(organization_id, user, db, ("owner", "admin"))
    member_user = db.query(User).filter(User.email == payload.email).first()
    if not member_user:
        raise HTTPException(status_code=404, detail="User not found")
    membership = TeamMember(organization_id=organization_id, user_id=member_user.id, role=payload.role)
    db.add(membership)
    audit(db, "team_member.added", user.id, organization_id, "user", str(member_user.id))
    db.commit()
    db.refresh(membership)
    return membership


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(UserSession).filter(UserSession.user_id == user.id).order_by(UserSession.created_at.desc()).all()


@router.get("/login-history", response_model=list[LoginHistoryResponse])
def login_history(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(LoginHistory).filter(LoginHistory.user_id == user.id).order_by(LoginHistory.created_at.desc()).limit(50).all()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def audit_logs(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
