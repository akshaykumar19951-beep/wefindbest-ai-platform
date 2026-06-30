from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str | None = Field(default=None, min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class EmailVerificationRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class APIKeyCreateRequest(BaseModel):
    name: str = Field(default="Default", min_length=1, max_length=120)
    organization_id: int | None = None


class APIKeyRotateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=80, pattern="^[a-z0-9-]+$")


class TeamMemberInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(member|admin|owner)$")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    api_key: str
    email_verification_token: str | None = None


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class APIKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    key: str | None = None
    is_active: bool
    organization_id: int | None = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    ip_address: str | None
    user_agent: str | None
    is_active: bool
    expires_at: datetime
    created_at: datetime | None
    last_seen_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryResponse(BaseModel):
    id: int
    email: EmailStr
    success: str
    ip_address: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    organization_id: int | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    api_key: str
    role: str
    email_verified: bool
    quota: int
    used: int

    model_config = ConfigDict(from_attributes=True)
