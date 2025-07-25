"""add reset token fields to user

Revision ID: add_reset_token_fields_to_user
Revises: 949e4b99c611
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reset_token_fields_to_user'
down_revision = '949e4b99c611'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reset_token and reset_token_expires columns to users table
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove reset_token and reset_token_expires columns from users table
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token') 