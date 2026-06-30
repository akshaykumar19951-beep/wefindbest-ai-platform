"""auth upgrade

Revision ID: 20260630_0002
Revises: 20260630_0001
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa

revision = "20260630_0002"
down_revision = "20260630_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="user"))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    op.add_column("api_keys", sa.Column("name", sa.String(), nullable=False, server_default="Default"))
    op.add_column("api_keys", sa.Column("prefix", sa.String(), nullable=True))
    op.add_column("api_keys", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("api_keys", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("api_keys", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.add_column("api_keys", sa.Column("rotated_from_id", sa.Integer(), nullable=True))
    op.add_column("api_keys", sa.Column("last_used_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_api_keys_user_id"), "api_keys", ["user_id"], unique=False)
    op.create_index(op.f("ix_api_keys_prefix"), "api_keys", ["prefix"], unique=False)
    bind = op.get_bind()
    op.create_index(op.f("ix_api_keys_organization_id"), "api_keys", ["organization_id"], unique=False)
    if bind.dialect.name != "sqlite":
        op.create_foreign_key("fk_api_keys_organization_id", "api_keys", "organizations", ["organization_id"], ["id"])
        op.create_foreign_key("fk_api_keys_rotated_from_id", "api_keys", "api_keys", ["rotated_from_id"], ["id"])

    rows = bind.execute(sa.text("SELECT id, key FROM api_keys")).mappings().all()
    for row in rows:
        key = row["key"] or ""
        bind.execute(
            sa.text("UPDATE api_keys SET prefix = :prefix WHERE id = :id"),
            {"prefix": key[:12], "id": row["id"]},
        )
    if bind.dialect.name != "sqlite":
        op.alter_column("api_keys", "prefix", nullable=False)

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_team_members_id"), "team_members", ["id"], unique=False)
    op.create_index(op.f("ix_team_members_organization_id"), "team_members", ["organization_id"], unique=False)
    op.create_index(op.f("ix_team_members_user_id"), "team_members", ["user_id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_id"), "sessions", ["id"], unique=False)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_sessions_refresh_token_hash"), "sessions", ["refresh_token_hash"], unique=True)

    for table_name in ("email_verification_tokens", "password_reset_tokens"):
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f(f"ix_{table_name}_id"), table_name, ["id"], unique=False)
        op.create_index(op.f(f"ix_{table_name}_user_id"), table_name, ["user_id"], unique=False)
        op.create_index(op.f(f"ix_{table_name}_token_hash"), table_name, ["token_hash"], unique=True)

    op.create_table(
        "login_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("success", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_history_id"), "login_history", ["id"], unique=False)
    op.create_index(op.f("ix_login_history_user_id"), "login_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_login_history_email"), "login_history", ["email"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_organization_id"), "audit_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_organization_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_login_history_email"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_user_id"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_id"), table_name="login_history")
    op.drop_table("login_history")
    for table_name in ("password_reset_tokens", "email_verification_tokens"):
        op.drop_index(op.f(f"ix_{table_name}_token_hash"), table_name=table_name)
        op.drop_index(op.f(f"ix_{table_name}_user_id"), table_name=table_name)
        op.drop_index(op.f(f"ix_{table_name}_id"), table_name=table_name)
        op.drop_table(table_name)
    op.drop_index(op.f("ix_sessions_refresh_token_hash"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_team_members_user_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_organization_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_id"), table_name="team_members")
    op.drop_table("team_members")
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint("fk_api_keys_rotated_from_id", "api_keys", type_="foreignkey")
        op.drop_constraint("fk_api_keys_organization_id", "api_keys", type_="foreignkey")
    op.drop_index(op.f("ix_api_keys_organization_id"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_prefix"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_user_id"), table_name="api_keys")
    op.drop_column("api_keys", "last_used_at")
    op.drop_column("api_keys", "rotated_from_id")
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "is_active")
    op.drop_column("api_keys", "organization_id")
    op.drop_column("api_keys", "prefix")
    op.drop_column("api_keys", "name")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "role")
