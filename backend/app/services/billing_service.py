from collections import defaultdict, deque
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import BillingPlan, Coupon, Invoice, MonthlyUsage, Payment, Subscription, User

_rate_windows: dict[int, deque[datetime]] = defaultdict(deque)

DEFAULT_PLANS = [
    ("Free", "free", 0.0, 1000, 100000, 20, 1, 1, '["Mock gateway", "Community support"]'),
    ("Starter", "starter", 29.0, 25000, 2500000, 120, 3, 3, '["All providers", "Basic analytics"]'),
    ("Pro", "pro", 99.0, 150000, 15000000, 600, 10, 10, '["Fallback routing", "Advanced analytics"]'),
    ("Business", "business", 299.0, 750000, 75000000, 2500, 50, 50, '["SAML-ready orgs", "Priority support"]'),
    ("Enterprise", "enterprise", 999.0, 5000000, 500000000, 10000, 250, 500, '["Custom limits", "Dedicated support"]'),
]


def seed_default_plans(db: Session) -> None:
    for name, slug, price, requests, tokens, rate, keys, members, features in DEFAULT_PLANS:
        existing = db.query(BillingPlan).filter(BillingPlan.slug == slug).first()
        if existing:
            continue
        db.add(
            BillingPlan(
                name=name,
                slug=slug,
                monthly_price_usd=price,
                monthly_request_limit=requests,
                monthly_token_limit=tokens,
                rate_limit_per_minute=rate,
                api_key_limit=keys,
                team_member_limit=members,
                features=features,
            )
        )


def current_period(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.utcnow()
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    return start, end


def get_plan(db: Session, slug: str) -> BillingPlan:
    plan = db.query(BillingPlan).filter(BillingPlan.slug == slug, BillingPlan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def get_or_create_default_subscription(db: Session, user: User) -> Subscription:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.id.desc())
        .first()
    )
    if subscription:
        return subscription

    plan = get_plan(db, user.plan or "free")
    start, end = current_period()
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        current_period_start=start,
        current_period_end=end,
    )
    db.add(subscription)
    db.flush()
    return subscription


def get_or_create_monthly_usage(db: Session, user: User) -> MonthlyUsage:
    start, end = current_period()
    usage = (
        db.query(MonthlyUsage)
        .filter(MonthlyUsage.user_id == user.id, MonthlyUsage.period_start == start)
        .first()
    )
    if usage:
        return usage
    usage = MonthlyUsage(user_id=user.id, period_start=start, period_end=end)
    db.add(usage)
    db.flush()
    return usage


def check_rate_limit(user_id: int, limit: int) -> None:
    now = datetime.utcnow()
    window = _rate_windows[user_id]
    while window and (now - window[0]).total_seconds() >= 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    window.append(now)


def enforce_billing_limits(db: Session, user: User, estimated_tokens: int = 0) -> tuple[Subscription, MonthlyUsage]:
    subscription = get_or_create_default_subscription(db, user)
    usage = get_or_create_monthly_usage(db, user)
    plan = subscription.plan
    check_rate_limit(user.id, plan.rate_limit_per_minute)
    if usage.requests_used + 1 > plan.monthly_request_limit:
        raise HTTPException(status_code=403, detail="Monthly request quota exceeded")
    if usage.tokens_used + estimated_tokens > plan.monthly_token_limit:
        raise HTTPException(status_code=403, detail="Monthly token quota exceeded")
    return subscription, usage


def record_usage(db: Session, user: User, tokens: int, cost_usd: float) -> MonthlyUsage:
    usage = get_or_create_monthly_usage(db, user)
    usage.requests_used += 1
    usage.tokens_used += tokens
    usage.cost_usd = round(usage.cost_usd + cost_usd, 8)
    usage.updated_at = datetime.utcnow()
    return usage


def apply_coupon(db: Session, code: str | None) -> Coupon | None:
    if not code:
        return None
    coupon = db.query(Coupon).filter(Coupon.code == code, Coupon.active == True).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if coupon.max_redemptions and coupon.times_redeemed >= coupon.max_redemptions:
        raise HTTPException(status_code=400, detail="Coupon exhausted")
    if coupon.expires_at and coupon.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon expired")
    coupon.times_redeemed += 1
    return coupon


def calculate_discount(plan: BillingPlan, coupon: Coupon | None) -> float:
    if not coupon:
        return 0.0
    percent_discount = plan.monthly_price_usd * (coupon.percent_off / 100)
    return round(min(plan.monthly_price_usd, percent_discount + coupon.amount_off_usd), 2)


def create_invoice_and_payment(db: Session, subscription: Subscription) -> tuple[Invoice, Payment | None]:
    plan = subscription.plan
    discount = calculate_discount(plan, subscription.coupon)
    total = round(max(0.0, plan.monthly_price_usd - discount), 2)
    invoice = Invoice(
        user_id=subscription.user_id,
        subscription_id=subscription.id,
        invoice_number=f"INV-{uuid4().hex[:10].upper()}",
        status="paid" if total == 0 else "open",
        subtotal_usd=plan.monthly_price_usd,
        discount_usd=discount,
        total_usd=total,
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
        paid_at=datetime.utcnow() if total == 0 else None,
    )
    db.add(invoice)
    db.flush()
    payment = None
    if total > 0:
        payment = Payment(
            user_id=subscription.user_id,
            invoice_id=invoice.id,
            amount_usd=total,
            status="succeeded",
            provider="mock",
            provider_payment_id=f"mock_{uuid4().hex[:12]}",
        )
        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        db.add(payment)
    return invoice, payment


def subscribe_user(db: Session, user: User, plan_slug: str, coupon_code: str | None = None) -> Subscription:
    plan = get_plan(db, plan_slug)
    coupon = apply_coupon(db, coupon_code)
    start, end = current_period()
    existing = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.id.desc())
        .first()
    )
    if existing:
        existing.status = "replaced"
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        current_period_start=start,
        current_period_end=end,
        coupon_id=coupon.id if coupon else None,
    )
    user.plan = plan.slug
    user.quota = plan.monthly_request_limit
    db.add(subscription)
    db.flush()
    create_invoice_and_payment(db, subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def create_coupon(db: Session, code: str, percent_off: int, amount_off_usd: float, max_redemptions: int | None):
    coupon = Coupon(
        code=code.upper(),
        percent_off=percent_off,
        amount_off_usd=amount_off_usd,
        max_redemptions=max_redemptions,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon
