from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    monthly_price_usd: float
    monthly_request_limit: int
    monthly_token_limit: int
    rate_limit_per_minute: int
    api_key_limit: int
    team_member_limit: int
    features: str

    model_config = ConfigDict(from_attributes=True)


class SubscribeRequest(BaseModel):
    plan_slug: str = Field(pattern="^(free|starter|pro|business|enterprise)$")
    coupon_code: str | None = Field(default=None, max_length=64)


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    percent_off: int = Field(default=0, ge=0, le=100)
    amount_off_usd: float = Field(default=0.0, ge=0)
    max_redemptions: int | None = Field(default=None, ge=1)


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    plan: PlanResponse

    model_config = ConfigDict(from_attributes=True)


class MonthlyUsageResponse(BaseModel):
    requests_used: int
    tokens_used: int
    cost_usd: float
    request_limit: int
    token_limit: int
    rate_limit_per_minute: int
    period_start: datetime
    period_end: datetime


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    status: str
    subtotal_usd: float
    discount_usd: float
    total_usd: float
    period_start: datetime
    period_end: datetime
    created_at: datetime | None
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount_usd: float
    status: str
    provider: str
    provider_payment_id: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CouponResponse(BaseModel):
    id: int
    code: str
    percent_off: int
    amount_off_usd: float
    max_redemptions: int | None
    times_redeemed: int
    active: bool

    model_config = ConfigDict(from_attributes=True)
