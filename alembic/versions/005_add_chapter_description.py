"""add chapter description

Revision ID: 005_add_chapter_description
Revises: 004_providers_list_policy
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_add_chapter_description"
down_revision: Union[str, None] = "004_providers_list_policy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chapters", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("chapters", "description")
