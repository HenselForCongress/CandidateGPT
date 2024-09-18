"""Fix dumb schema mistakes... whoops

Revision ID: 49541176cb75
Revises: fc52216bb119
Create Date: 2024-09-17 22:58:31.147128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49541176cb75'
down_revision: Union[str, None] = 'fc52216bb119'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the query_id column from the responses table
    with op.batch_alter_table('responses', schema='logs') as batch_op:
        batch_op.drop_column('query_id')

def downgrade() -> None:
    # Add the query_id column back to the responses table
    with op.batch_alter_table('responses', schema='logs') as batch_op:
        batch_op.add_column(sa.Column('query_id', sa.Integer, sa.ForeignKey('logs.queries.id', ondelete='CASCADE'), nullable=True, comment="Associated query ID"))
