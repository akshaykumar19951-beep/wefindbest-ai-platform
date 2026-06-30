from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_jwt_user, require_roles
from app.core.deps import get_db
from app.db.models import Coupon, Invoice, Payment, Subscription, User
from app.db.models.billing import BillingPlan
from app.schemas.billing import (
    CouponCreateRequest,
    CouponResponse,
    InvoiceResponse,
    MonthlyUsageResponse,
    PaymentResponse,
    PlanResponse,
    SubscribeRequest,
    SubscriptionResponse,
)
from app.services.billing_service import (
    create_coupon,
    get_or_create_default_subscription,
    get_or_create_monthly_usage,
    subscribe_user,
)

router = APIRouter()


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return db.query(BillingPlan).filter(BillingPlan.is_active == True).order_by(BillingPlan.monthly_price_usd.asc()).all()


@router.get("/subscription", response_model=SubscriptionResponse)
def current_subscription(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    subscription = get_or_create_default_subscription(db, user)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(payload: SubscribeRequest, user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return subscribe_user(db, user, payload.plan_slug, payload.coupon_code)


@router.get("/usage", response_model=MonthlyUsageResponse)
def usage(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    subscription = get_or_create_default_subscription(db, user)
    usage_record = get_or_create_monthly_usage(db, user)
    db.commit()
    return {
        "requests_used": usage_record.requests_used,
        "tokens_used": usage_record.tokens_used,
        "cost_usd": usage_record.cost_usd,
        "request_limit": subscription.plan.monthly_request_limit,
        "token_limit": subscription.plan.monthly_token_limit,
        "rate_limit_per_minute": subscription.plan.rate_limit_per_minute,
        "period_start": usage_record.period_start,
        "period_end": usage_record.period_end,
    }


@router.get("/invoices", response_model=list[InvoiceResponse])
def invoices(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(Invoice).filter(Invoice.user_id == user.id).order_by(Invoice.created_at.desc()).all()


@router.get("/payments", response_model=list[PaymentResponse])
def payments(user: User = Depends(get_current_jwt_user), db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.created_at.desc()).all()


@router.get("/coupons", response_model=list[CouponResponse])
def coupons(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("/coupons", response_model=CouponResponse)
def create_coupon_route(
    payload: CouponCreateRequest,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return create_coupon(db, payload.code, payload.percent_off, payload.amount_off_usd, payload.max_redemptions)
