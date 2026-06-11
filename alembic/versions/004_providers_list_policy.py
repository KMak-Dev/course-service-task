"""allow listing all providers

Revision ID: 004_providers_list_policy
Revises: 003_add_providers
Create Date: 2026-06-10

"""

from typing import Sequence, Union

from alembic import op

revision: str = "004_providers_list_policy"
down_revision: Union[str, None] = "003_add_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP POLICY IF EXISTS providers_tenant_isolation ON providers")
    op.execute(
        """
        CREATE POLICY providers_select_all ON providers
          FOR SELECT
          USING (true)
        """
    )
    op.execute(
        """
        CREATE POLICY providers_insert_tenant ON providers
          FOR INSERT
          WITH CHECK (id = current_setting('app.current_provider_id', true)::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY providers_update_tenant ON providers
          FOR UPDATE
          USING (id = current_setting('app.current_provider_id', true)::uuid)
          WITH CHECK (id = current_setting('app.current_provider_id', true)::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY providers_delete_tenant ON providers
          FOR DELETE
          USING (id = current_setting('app.current_provider_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS providers_delete_tenant ON providers")
    op.execute("DROP POLICY IF EXISTS providers_update_tenant ON providers")
    op.execute("DROP POLICY IF EXISTS providers_insert_tenant ON providers")
    op.execute("DROP POLICY IF EXISTS providers_select_all ON providers")
    op.execute(
        """
        CREATE POLICY providers_tenant_isolation ON providers
          FOR ALL
          USING (id = current_setting('app.current_provider_id', true)::uuid)
          WITH CHECK (id = current_setting('app.current_provider_id', true)::uuid)
        """
    )
