"""add processing error information

Revision ID: 036e9a8fa95d
Revises: ab5003c36a33
Create Date: 2026-10-09 00:10:13.656391
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "036e9a8fa95d"
down_revision: Union[str, Sequence[str], None] = "ab5003c36a33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "file_info", sa.Column("error_message", sa.String(length=1000), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("file_info", "error_message")
