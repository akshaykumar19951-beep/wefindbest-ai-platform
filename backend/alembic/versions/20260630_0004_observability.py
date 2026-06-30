"""observability

Revision ID: 20260630_0004
Revises: 20260630_0003
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa

revision = "20260630_0004"
down_revision = "20260630_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "request_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("api_key_prefix", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_request_logs_id"), "request_logs", ["id"], unique=False)
    op.create_index(op.f("ix_request_logs_request_id"), "request_logs", ["request_id"], unique=False)
    op.create_index(op.f("ix_request_logs_method"), "request_logs", ["method"], unique=False)
    op.create_index(op.f("ix_request_logs_path"), "request_logs", ["path"], unique=False)
    op.create_index(op.f("ix_request_logs_status_code"), "request_logs", ["status_code"], unique=False)
    op.create_index(op.f("ix_request_logs_user_id"), "request_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_request_logs_created_at"), "request_logs", ["created_at"], unique=False)

    op.create_table(
        "error_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_log_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stack", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["request_log_id"], ["request_logs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_error_events_id"), "error_events", ["id"], unique=False)
    op.create_index(op.f("ix_error_events_request_log_id"), "error_events", ["request_log_id"], unique=False)
    op.create_index(op.f("ix_error_events_user_id"), "error_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_error_events_path"), "error_events", ["path"], unique=False)
    op.create_index(op.f("ix_error_events_status_code"), "error_events", ["status_code"], unique=False)
    op.create_index(op.f("ix_error_events_created_at"), "error_events", ["created_at"], unique=False)

    op.create_table(
        "user_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_activity_id"), "user_activity", ["id"], unique=False)
    op.create_index(op.f("ix_user_activity_user_id"), "user_activity", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_activity_action"), "user_activity", ["action"], unique=False)
    op.create_index(op.f("ix_user_activity_created_at"), "user_activity", ["created_at"], unique=False)

    op.create_table(
        "provider_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_provider_metrics_id"), "provider_metrics", ["id"], unique=False)
    op.create_index(op.f("ix_provider_metrics_user_id"), "provider_metrics", ["user_id"], unique=False)
    op.create_index(op.f("ix_provider_metrics_provider"), "provider_metrics", ["provider"], unique=False)
    op.create_index(op.f("ix_provider_metrics_model"), "provider_metrics", ["model"], unique=False)
    op.create_index(op.f("ix_provider_metrics_success"), "provider_metrics", ["success"], unique=False)
    op.create_index(op.f("ix_provider_metrics_created_at"), "provider_metrics", ["created_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_alerts_source"), "alerts", ["source"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_status"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_source"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_severity"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_provider_metrics_created_at"), table_name="provider_metrics")
    op.drop_index(op.f("ix_provider_metrics_success"), table_name="provider_metrics")
    op.drop_index(op.f("ix_provider_metrics_model"), table_name="provider_metrics")
    op.drop_index(op.f("ix_provider_metrics_provider"), table_name="provider_metrics")
    op.drop_index(op.f("ix_provider_metrics_user_id"), table_name="provider_metrics")
    op.drop_index(op.f("ix_provider_metrics_id"), table_name="provider_metrics")
    op.drop_table("provider_metrics")
    op.drop_index(op.f("ix_user_activity_created_at"), table_name="user_activity")
    op.drop_index(op.f("ix_user_activity_action"), table_name="user_activity")
    op.drop_index(op.f("ix_user_activity_user_id"), table_name="user_activity")
    op.drop_index(op.f("ix_user_activity_id"), table_name="user_activity")
    op.drop_table("user_activity")
    op.drop_index(op.f("ix_error_events_created_at"), table_name="error_events")
    op.drop_index(op.f("ix_error_events_status_code"), table_name="error_events")
    op.drop_index(op.f("ix_error_events_path"), table_name="error_events")
    op.drop_index(op.f("ix_error_events_user_id"), table_name="error_events")
    op.drop_index(op.f("ix_error_events_request_log_id"), table_name="error_events")
    op.drop_index(op.f("ix_error_events_id"), table_name="error_events")
    op.drop_table("error_events")
    op.drop_index(op.f("ix_request_logs_created_at"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_user_id"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_status_code"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_path"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_method"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_request_id"), table_name="request_logs")
    op.drop_index(op.f("ix_request_logs_id"), table_name="request_logs")
    op.drop_table("request_logs")
