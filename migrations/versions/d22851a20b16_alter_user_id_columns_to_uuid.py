"""Alter user_id columns to UUID

Revision ID: d22851a20b16
Revises: 19b8149e8272
Create Date: 2024-09-17 19:43:32.444728

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd22851a20b16'
down_revision: Union[str, None] = '19b8149e8272'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # For 'logs.activity' table
    op.alter_column('activity', 'user_id',
               existing_type=sa.Integer(),
               type_=postgresql.UUID(as_uuid=True),
               existing_nullable=False,
               schema='logs')

    # For 'logs.queries' table
    op.alter_column('queries', 'user_id',
               existing_type=sa.Integer(),
               type_=postgresql.UUID(as_uuid=True),
               existing_nullable=False,
               schema='logs')

    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # For 'logs.activity' table
    op.alter_column('activity', 'user_id',
               existing_type=postgresql.UUID(as_uuid=True),
               type_=sa.Integer(),
               existing_nullable=False,
               schema='logs')

    # For 'logs.queries' table
    op.alter_column('queries', 'user_id',
               existing_type=postgresql.UUID(as_uuid=True),
               type_=sa.Integer(),
               existing_nullable=False,
               schema='logs')

    # ### end Alembic commands ###
