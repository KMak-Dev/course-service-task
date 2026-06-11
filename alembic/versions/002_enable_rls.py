"""enable row level security

Revision ID: 002_enable_rls
Revises: 001_initial_schema
Create Date: 2026-06-10

"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_enable_rls"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = ("courses", "chapters", "lessons", "lesson_videos")

POLICY_SQL = """
CREATE POLICY {policy_name} ON {table_name}
  FOR ALL
  USING (provider_id = current_setting('app.current_provider_id', true)::uuid)
  WITH CHECK (provider_id = current_setting('app.current_provider_id', true)::uuid)
"""


def upgrade() -> None:
    for table_name in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
        op.execute(
            POLICY_SQL.format(
                policy_name=f"{table_name}_tenant_isolation",
                table_name=table_name,
            )
        )


def downgrade() -> None:
    for table_name in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name}")
        op.execute(f"ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")
