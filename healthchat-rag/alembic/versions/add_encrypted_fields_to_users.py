"""Add encrypted fields to users table

Revision ID: add_encrypted_fields_to_users
Revises: add_role_field_to_users
Create Date: 2024-01-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_encrypted_fields_to_users'
down_revision = 'add_role_field_to_users'
branch_labels = None
depends_on = None

def upgrade():
    # Add encrypted PII fields
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.String(), nullable=True))
    op.add_column('users', sa.Column('emergency_contact', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('insurance_info', sa.Text(), nullable=True))
    
    # Add encrypted health data fields
    op.add_column('users', sa.Column('blood_type', sa.String(), nullable=True))
    op.add_column('users', sa.Column('allergies', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('family_history', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('diagnoses', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('symptoms', sa.Text(), nullable=True))

def downgrade():
    # Remove encrypted fields
    op.drop_column('users', 'symptoms')
    op.drop_column('users', 'diagnoses')
    op.drop_column('users', 'family_history')
    op.drop_column('users', 'allergies')
    op.drop_column('users', 'blood_type')
    op.drop_column('users', 'insurance_info')
    op.drop_column('users', 'emergency_contact')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'address')
    op.drop_column('users', 'phone') 