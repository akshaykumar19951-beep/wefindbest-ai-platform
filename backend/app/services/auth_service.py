import json
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.api_key import generate_api_key
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_opaque_token,
    hash_token,
)
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.models import (
    APIKey,
    AuditLog,
    EmailVerificationToken,
    LoginHistory,
    Organization,
    PasswordResetToken,
    Session as UserSession,
    TeamMember,
    User,
)
from app.services.billing_service import get_or_create_default_subscription


def audit(
    db: Session,
    action: str,
    actor_user_id: int | None = None,
    organization_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}),
            ip_address=ip_address,
        )
    )


def create_api_key(
    db: Session,
    user: User,
    name: str = "Default",
    organization_id: int | None = None,
) -> tuple[APIKey, str]:
    key = generate_api_key()
    api_key = APIKey(
        name=name,
        key=key,
        prefix=key[:12],
        user_id=user.id,
        organization_id=organization_id,
    )
    db.add(api_key)
    return api_key, key


def create_session(
    db: Session,
    user: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[UserSession, str]:
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    return session, refresh_token


def create_email_verification_token(db: Session, user: User) -> str:
    token = generate_opaque_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS),
        )
    )
    return token


def register_user(
    db: Session,
    email: str,
    password: str,
    organization_name: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    role = "admin" if db.query(User).count() == 0 else "user"
    user = User(
        email=email,
        hashed_password=hash_password(password),
        api_key=generate_api_key(),
        role=role,
        quota=settings.DEFAULT_USER_QUOTA,
        used=0,
    )
    db.add(user)
    db.flush()

    organization = None
    if organization_name:
        slug = organization_name.lower().strip().replace(" ", "-")
        organization = Organization(name=organization_name, slug=slug)
        db.add(organization)
        db.flush()
        db.add(TeamMember(organization_id=organization.id, user_id=user.id, role="owner"))

    api_key, raw_api_key = create_api_key(
        db,
        user,
        name="Default",
        organization_id=organization.id if organization else None,
    )
    user.api_key = raw_api_key
    session, refresh_token = create_session(db, user, ip_address, user_agent)
    get_or_create_default_subscription(db, user)
    verification_token = create_email_verification_token(db, user)
    audit(db, "user.registered", user.id, organization.id if organization else None, "user", str(user.id), ip_address=ip_address)
    db.add(LoginHistory(user_id=user.id, email=user.email, success="success", ip_address=ip_address, user_agent=user_agent))
    db.commit()
    db.refresh(user)
    db.refresh(api_key)

    return {
        "access_token": create_access_token({"sub": user.email, "user_id": user.id, "role": user.role}),
        "refresh_token": refresh_token,
        "api_key": raw_api_key,
        "email_verification_token": verification_token,
    }


def login_user(
    db: Session,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        db.add(LoginHistory(user_id=user.id if user else None, email=email, success="failure", ip_address=ip_address, user_agent=user_agent))
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session, refresh_token = create_session(db, user, ip_address, user_agent)
    db.add(LoginHistory(user_id=user.id, email=user.email, success="success", ip_address=ip_address, user_agent=user_agent))
    audit(db, "user.login", user.id, resource_type="session", resource_id=str(session.id), ip_address=ip_address)
    db.commit()

    active_key = (
        db.query(APIKey)
        .filter(APIKey.user_id == user.id, APIKey.is_active == True)
        .order_by(APIKey.id.asc())
        .first()
    )
    raw_api_key = active_key.key if active_key else user.api_key

    return {
        "access_token": create_access_token({"sub": user.email, "user_id": user.id, "role": user.role}),
        "refresh_token": refresh_token,
        "api_key": raw_api_key,
        "email_verification_token": None,
    }


def refresh_session(db: Session, refresh_token: str):
    try:
        payload = decode_refresh_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_hash = hash_token(refresh_token)
    session = (
        db.query(UserSession)
        .filter(UserSession.refresh_token_hash == token_hash, UserSession.is_active == True)
        .first()
    )
    if not session or session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    session.is_active = False
    session.revoked_at = datetime.utcnow()
    new_session, new_refresh = create_session(db, user, session.ip_address, session.user_agent)
    audit(db, "session.refreshed", user.id, resource_type="session", resource_id=str(new_session.id))
    db.commit()

    return {
        "access_token": create_access_token({"sub": user.email, "user_id": user.id, "role": user.role}),
        "refresh_token": new_refresh,
    }


def revoke_session(db: Session, refresh_token: str, actor_user_id: int | None = None):
    session = db.query(UserSession).filter(UserSession.refresh_token_hash == hash_token(refresh_token)).first()
    if session:
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        audit(db, "session.revoked", actor_user_id or session.user_id, resource_type="session", resource_id=str(session.id))
        db.commit()


def verify_email(db: Session, token: str) -> None:
    record = db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == hash_token(token)).first()
    if not record or record.used or record.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.email_verified = True
    record.used = True
    audit(db, "user.email_verified", user.id, resource_type="user", resource_id=str(user.id))
    db.commit()


def request_password_reset(db: Session, email: str) -> str | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    token = generate_opaque_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    audit(db, "password_reset.requested", user.id, resource_type="user", resource_id=str(user.id))
    db.commit()
    return token


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_token(token)).first()
    if not record or record.used or record.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(new_password)
    record.used = True
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_active": False, "revoked_at": datetime.utcnow()})
    audit(db, "password_reset.completed", user.id, resource_type="user", resource_id=str(user.id))
    db.commit()
