"""remove mfa columns

Revision ID: 20260619_01
Revises: 20260617_02
Create Date: 2026-06-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260619_01'
down_revision = '20260617_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop MFA columns from users table
    op.drop_column('users', 'mfa_recovery_codes')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'mfa_secret')


def downgrade() -> None:
    # Re-add MFA columns to users table
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('mfa_recovery_codes', sa.JSON(), nullable=True))
