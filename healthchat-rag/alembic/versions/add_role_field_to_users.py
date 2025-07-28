"""Add role field to users table

Revision ID: add_role_field_to_users
Revises: 949e4b99c611
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_role_field_to_users'
down_revision = '949e4b99c611'
branch_labels = None
depends_on = None

def upgrade():
    # Add role column to users table
    op.add_column('users', sa.Column('role', sa.String(), nullable=True, server_default='patient'))
    
    # Update existing users to have 'patient' role
    op.execute("UPDATE users SET role = 'patient' WHERE role IS NULL")
    
    # Make role column not nullable after setting default values
    op.alter_column('users', 'role', nullable=False)

def downgrade():
    # Remove role column from users table
    op.drop_column('users', 'role') 