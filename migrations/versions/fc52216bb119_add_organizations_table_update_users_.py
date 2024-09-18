"""Add organizations table, update users with names, organization, and notes

Revision ID: fc52216bb119
Revises: 240523c19add
Create Date: 2024-09-17 22:31:59.583842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fc52216bb119'
down_revision: Union[str, None] = '240523c19add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create 'organizations' table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment="Auto incrementing primary key"),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True, comment="Name of the organization"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="Record creation date"),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="Record last update date"),
        schema='entities'
    )

    # Add new columns to 'users' table
    with op.batch_alter_table('users', schema='entities') as batch_op:
        # Set a default value for 'given_name' during the addition
        batch_op.add_column(sa.Column('given_name', sa.String(length=255), nullable=False, server_default='Unknown', comment="User's given name"))
        batch_op.add_column(sa.Column('family_name', sa.String(length=255), nullable=True, comment="User's family name (if applicable)"))
        batch_op.add_column(sa.Column('preferred_name', sa.String(length=255), nullable=True, comment="User's preferred name"))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True, comment="Notes about the user, including how they plan to use the tool"))
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), sa.ForeignKey('entities.organizations.id', ondelete='SET NULL'), nullable=True, comment="Foreign key to the organization"))

    # Remove the default value for 'given_name' (if desired)
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('given_name', server_default=None)


def downgrade() -> None:
    # Remove columns from 'users' table
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.drop_column('organization_id')
        batch_op.drop_column('notes')
        batch_op.drop_column('preferred_name')
        batch_op.drop_column('family_name')
        batch_op.drop_column('given_name')

    # Drop 'organizations' table
    op.drop_table('organizations', schema='entities')
