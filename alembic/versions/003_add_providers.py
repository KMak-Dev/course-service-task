"""add providers table

Revision ID: 003_add_providers
Revises: 002_enable_rls
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_add_providers"
down_revision: Union[str, None] = "002_enable_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_FK_TABLES = ("courses", "chapters", "lessons", "lesson_videos")


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
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
    )

    for table_name in TENANT_FK_TABLES:
        op.create_foreign_key(
            f"fk_{table_name}_provider_id",
            table_name,
            "providers",
            ["provider_id"],
            ["id"],
        )

    op.execute("ALTER TABLE providers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE providers FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY providers_tenant_isolation ON providers
          FOR ALL
          USING (id = current_setting('app.current_provider_id', true)::uuid)
          WITH CHECK (id = current_setting('app.current_provider_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS providers_tenant_isolation ON providers")
    op.execute("ALTER TABLE providers NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE providers DISABLE ROW LEVEL SECURITY")

    for table_name in reversed(TENANT_FK_TABLES):
        op.drop_constraint(f"fk_{table_name}_provider_id", table_name, type_="foreignkey")

    op.drop_table("providers")
