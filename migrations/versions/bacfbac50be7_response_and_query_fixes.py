"""Response and query fixes

Revision ID: bacfbac50be7
Revises: 49541176cb75
Create Date: 2024-09-17 23:19:28.770220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bacfbac50be7'
down_revision: Union[str, None] = '49541176cb75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the response_text column from the queries table
    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.drop_column('response_text')

    # Add the response_id column to the queries table
    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.add_column(sa.Column('response_id', sa.Integer(), sa.ForeignKey('logs.responses.id', ondelete='CASCADE'), nullable=True))


def downgrade() -> None:
    # Add the response_text column back to the queries table
    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.add_column(sa.Column('response_text', sa.Text(), nullable=False))

    # Remove the response_id column from the queries table
    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.drop_column('response_id')
