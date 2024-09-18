"""Rename _is_active to is_active

Revision ID: 240523c19add
Revises: 3322d400bce8
Create Date: 2024-09-17 20:40:16.827841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '240523c19add'
down_revision: Union[str, None] = '3322d400bce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename the column back to 'is_active'
    op.alter_column('users', '_is_active', new_column_name='is_active', schema='entities')

def downgrade():
    # Reverse the change if necessary
    op.alter_column('users', 'is_active', new_column_name='_is_active', schema='entities')
