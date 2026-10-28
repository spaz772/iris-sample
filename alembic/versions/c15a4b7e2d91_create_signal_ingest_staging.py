"""create iris staging signal ingest table

Revision ID: c15a4b7e2d91
Revises: b18ad888465f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "c15a4b7e2d91"
down_revision: Union[str, Sequence[str], None] = "b18ad888465f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS iris_staging")
    op.create_table(
        "signal_ingest",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("signal_type", sa.String(length=100), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("location_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column(
            "geometry",
            Geometry(geometry_type="POINT", srid=25832, spatial_index=False),
            nullable=True,
        ),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quality_status", sa.String(length=50), nullable=False),
        sa.Column("quality_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("matched_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source", "source_id", name="uq_signal_ingest_source_source_id"
        ),
        schema="iris_staging",
    )
    op.create_index(
        "idx_signal_ingest_signal_type",
        "signal_ingest",
        ["signal_type"],
        schema="iris_staging",
    )
    op.create_index(
        "idx_signal_ingest_status",
        "signal_ingest",
        ["status"],
        schema="iris_staging",
    )
    op.create_index(
        "idx_signal_ingest_geometry",
        "signal_ingest",
        ["geometry"],
        schema="iris_staging",
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_signal_ingest_geometry",
        table_name="signal_ingest",
        schema="iris_staging",
        postgresql_using="gist",
    )
    op.drop_index(
        "idx_signal_ingest_status",
        table_name="signal_ingest",
        schema="iris_staging",
    )
    op.drop_index(
        "idx_signal_ingest_signal_type",
        table_name="signal_ingest",
        schema="iris_staging",
    )
    op.drop_table("signal_ingest", schema="iris_staging")
