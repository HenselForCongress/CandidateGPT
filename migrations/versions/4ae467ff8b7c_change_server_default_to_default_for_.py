"""Change server_default to default for timestamp columns

Revision ID: 4ae467ff8b7c
Revises: bacfbac50be7
Create Date: 2024-09-18 05:12:26.446569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision: str = '4ae467ff8b7c'
down_revision: Union[str, None] = 'bacfbac50be7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Update the 'created_at' and 'updated_at' columns in each table to use default instead of server_default
    with op.batch_alter_table('user_types', schema='meta') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

    with op.batch_alter_table('organizations', schema='entities') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

    with op.batch_alter_table('responses', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

    with op.batch_alter_table('activity', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

def downgrade() -> None:
    # Restore the 'created_at' and 'updated_at' columns in each table to use server_default
    with op.batch_alter_table('user_types', schema='meta') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())

    with op.batch_alter_table('organizations', schema='entities') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())

    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())

    with op.batch_alter_table('queries', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())

    with op.batch_alter_table('responses', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())

    with op.batch_alter_table('activity', schema='logs') as batch_op:
        batch_op.alter_column('created_at', server_default=sa.func.now())
        batch_op.alter_column('updated_at', server_default=sa.func.now())
