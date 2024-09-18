"""Fields

Revision ID: e7743a2322cb
Revises: 4ae467ff8b7c
Create Date: 2024-09-18 05:22:56.194413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7743a2322cb'
down_revision: Union[str, None] = '4ae467ff8b7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Make `given_name` and other fields nullable in the User table
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('given_name', existing_type=sa.String(255), nullable=True)
        batch_op.alter_column('created_at', existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column('updated_at', existing_type=sa.DateTime(), nullable=False)

def downgrade():
    # Revert `given_name` to non-nullable in the User table
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('given_name', existing_type=sa.String(255), nullable=False)
        batch_op.alter_column('created_at', existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column('updated_at', existing_type=sa.DateTime(), nullable=False)
