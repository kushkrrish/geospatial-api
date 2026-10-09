"""add geospatial feature measurements

Revision ID: ab5003c36a33
Revises: a28a7f3312f7
Create Date: 2026-10-08 23:35:55.460171
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "ab5003c36a33"
down_revision: Union[str, Sequence[str], None] = "a28a7f3312f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "features",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("feature_index", sa.Integer(), nullable=False),
        sa.Column("geometry_type", sa.String(length=50), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="GEOMETRY", srid=4326, spatial_index=False
            ),
            nullable=False,
        ),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["file_info.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_features_geometry", "features", ["geometry"], unique=False,
        postgresql_using="gist"
    )
    op.create_index(op.f("ix_features_file_id"), "features", ["file_id"], unique=False)
    op.add_column("file_info", sa.Column("source_crs", sa.String(length=50), nullable=True))
    op.add_column("file_info", sa.Column("feature_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("file_info", "feature_count")
    op.drop_column("file_info", "source_crs")
    op.drop_index(op.f("ix_features_file_id"), table_name="features")
    op.drop_index("idx_features_geometry", table_name="features", postgresql_using="gist")
    op.drop_table("features")
