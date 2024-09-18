"""Rename is_active column to _is_active

Revision ID: 3322d400bce8
Revises: 91989d63b5c9
Create Date: 2024-09-17 20:13:52.639817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3322d400bce8'
down_revision: Union[str, None] = '91989d63b5c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the 'is_active' column to '_is_active'
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('is_active', new_column_name='_is_active')


def downgrade() -> None:
    # Revert the column name change in case of a downgrade
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('_is_active', new_column_name='is_active')
