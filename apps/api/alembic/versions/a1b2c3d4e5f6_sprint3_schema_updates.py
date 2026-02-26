"""sprint3_schema_updates

Revision ID: a1b2c3d4e5f6
Revises: 5502d0130dfa
Create Date: 2026-02-25

Adds Sprint 3 columns:
- organizations: grace_period_end, onboarding_completed
- invitations: rename user_type -> invite_type, add project_ids, sub_company_id,
  owner_account_id, invited_by, accepted_at; fix status default case
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5502d0130dfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- organizations: add grace_period_end and onboarding_completed ----
    op.add_column(
        'organizations',
        sa.Column('grace_period_end', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        'organizations',
        sa.Column(
            'onboarding_completed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # ---- invitations: rename user_type -> invite_type ----
    op.alter_column(
        'invitations',
        'user_type',
        new_column_name='invite_type',
    )

    # ---- invitations: fix status default from 'PENDING' to 'pending' ----
    op.alter_column(
        'invitations',
        'status',
        server_default=sa.text("'pending'"),
    )
    # Update any existing rows that have uppercase status
    op.execute("UPDATE invitations SET status = LOWER(status) WHERE status != LOWER(status)")

    # ---- invitations: add missing columns ----
    op.add_column(
        'invitations',
        sa.Column(
            'project_ids',
            postgresql.JSONB(),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        'invitations',
        sa.Column(
            'sub_company_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('sub_companies.id'),
            nullable=True,
        ),
    )
    op.add_column(
        'invitations',
        sa.Column(
            'owner_account_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('owner_accounts.id'),
            nullable=True,
        ),
    )
    op.add_column(
        'invitations',
        sa.Column(
            'invited_by',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        'invitations',
        sa.Column(
            'accepted_at',
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # ---- invitations: remove added columns ----
    op.drop_column('invitations', 'accepted_at')
    op.drop_column('invitations', 'invited_by')
    op.drop_column('invitations', 'owner_account_id')
    op.drop_column('invitations', 'sub_company_id')
    op.drop_column('invitations', 'project_ids')

    # ---- invitations: revert status default ----
    op.alter_column(
        'invitations',
        'status',
        server_default=sa.text("'PENDING'"),
    )

    # ---- invitations: rename invite_type back to user_type ----
    op.alter_column(
        'invitations',
        'invite_type',
        new_column_name='user_type',
    )

    # ---- organizations: remove Sprint 3 columns ----
    op.drop_column('organizations', 'onboarding_completed')
    op.drop_column('organizations', 'grace_period_end')
