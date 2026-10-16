"""add Cloud Shield security analysis tables

Revision ID: 4f2c1e7d9a10
Revises: 18c176c7131b
"""

from alembic import op
import sqlalchemy as sa


revision = "4f2c1e7d9a10"
down_revision = "18c176c7131b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitored_sites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("technology", sa.String()),
        sa.Column("region", sa.String()),
        sa.Column("tls_expiry", sa.String()),
        sa.Column("last_scan_at", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_table(
        "security_scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("scan_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("log_count", sa.Integer()),
        sa.Column("request_count", sa.Integer()),
        sa.Column("blocked_count", sa.Integer()),
        sa.ForeignKeyConstraint(["site_id"], ["monitored_sites.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_key"),
    )
    op.create_table(
        "security_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("finding_key", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("evidence", sa.JSON()),
        sa.Column("status", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["security_scans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_key"),
    )
    op.create_table(
        "log_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("event_key", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime()),
        sa.Column("method", sa.String()),
        sa.Column("path", sa.String()),
        sa.Column("status_code", sa.Integer()),
        sa.Column("source_ip", sa.String()),
        sa.Column("action", sa.String()),
        sa.Column("severity", sa.String()),
        sa.ForeignKeyConstraint(["scan_id"], ["security_scans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key"),
    )


def downgrade() -> None:
    op.drop_table("log_events")
    op.drop_table("security_findings")
    op.drop_table("security_scans")
    op.drop_table("monitored_sites")