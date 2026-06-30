"""subscription billing

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa

revision = "20260630_0003"
down_revision = "20260630_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("monthly_price_usd", sa.Float(), nullable=False),
        sa.Column("monthly_request_limit", sa.Integer(), nullable=False),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
        sa.Column("api_key_limit", sa.Integer(), nullable=False),
        sa.Column("team_member_limit", sa.Integer(), nullable=False),
        sa.Column("features", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_billing_plans_id"), "billing_plans", ["id"], unique=False)
    op.create_index(op.f("ix_billing_plans_name"), "billing_plans", ["name"], unique=True)
    op.create_index(op.f("ix_billing_plans_slug"), "billing_plans", ["slug"], unique=True)

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("percent_off", sa.Integer(), nullable=False),
        sa.Column("amount_off_usd", sa.Float(), nullable=False),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("times_redeemed", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_coupons_id"), "coupons", ["id"], unique=False)
    op.create_index(op.f("ix_coupons_code"), "coupons", ["code"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_period_start", sa.DateTime(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("coupon_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["billing_plans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)
    op.create_index(op.f("ix_subscriptions_plan_id"), "subscriptions", ["plan_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("subtotal_usd", sa.Float(), nullable=False),
        sa.Column("discount_usd", sa.Float(), nullable=False),
        sa.Column("total_usd", sa.Float(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)
    op.create_index(op.f("ix_invoices_user_id"), "invoices", ["user_id"], unique=False)
    op.create_index(op.f("ix_invoices_subscription_id"), "invoices", ["subscription_id"], unique=False)
    op.create_index(op.f("ix_invoices_invoice_number"), "invoices", ["invoice_number"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("amount_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_payment_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_id"), "payments", ["id"], unique=False)
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)
    op.create_index(op.f("ix_payments_invoice_id"), "payments", ["invoice_id"], unique=False)

    op.create_table(
        "monthly_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("requests_used", sa.Integer(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_monthly_usage_id"), "monthly_usage", ["id"], unique=False)
    op.create_index(op.f("ix_monthly_usage_user_id"), "monthly_usage", ["user_id"], unique=False)
    op.create_index(op.f("ix_monthly_usage_period_start"), "monthly_usage", ["period_start"], unique=False)

    plans = [
        ("Free", "free", 0.0, 1000, 100000, 20, 1, 1, '["Mock gateway", "Community support"]'),
        ("Starter", "starter", 29.0, 25000, 2500000, 120, 3, 3, '["All providers", "Basic analytics"]'),
        ("Pro", "pro", 99.0, 150000, 15000000, 600, 10, 10, '["Fallback routing", "Advanced analytics"]'),
        ("Business", "business", 299.0, 750000, 75000000, 2500, 50, 50, '["SAML-ready orgs", "Priority support"]'),
        ("Enterprise", "enterprise", 999.0, 5000000, 500000000, 10000, 250, 500, '["Custom limits", "Dedicated support"]'),
    ]
    bind = op.get_bind()
    for plan in plans:
        bind.execute(
            sa.text(
                "INSERT INTO billing_plans "
                "(name, slug, monthly_price_usd, monthly_request_limit, monthly_token_limit, "
                "rate_limit_per_minute, api_key_limit, team_member_limit, features, is_active, created_at) "
                "VALUES (:name, :slug, :price, :requests, :tokens, :rate, :keys, :members, :features, :active, CURRENT_TIMESTAMP)"
            ),
            {
                "name": plan[0],
                "slug": plan[1],
                "price": plan[2],
                "requests": plan[3],
                "tokens": plan[4],
                "rate": plan[5],
                "keys": plan[6],
                "members": plan[7],
                "features": plan[8],
                "active": True,
            },
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_monthly_usage_period_start"), table_name="monthly_usage")
    op.drop_index(op.f("ix_monthly_usage_user_id"), table_name="monthly_usage")
    op.drop_index(op.f("ix_monthly_usage_id"), table_name="monthly_usage")
    op.drop_table("monthly_usage")
    op.drop_index(op.f("ix_payments_invoice_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_invoices_invoice_number"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_subscription_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_user_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_id"), table_name="invoices")
    op.drop_table("invoices")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_plan_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_coupons_code"), table_name="coupons")
    op.drop_index(op.f("ix_coupons_id"), table_name="coupons")
    op.drop_table("coupons")
    op.drop_index(op.f("ix_billing_plans_slug"), table_name="billing_plans")
    op.drop_index(op.f("ix_billing_plans_name"), table_name="billing_plans")
    op.drop_index(op.f("ix_billing_plans_id"), table_name="billing_plans")
    op.drop_table("billing_plans")
