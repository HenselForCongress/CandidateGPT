"""Ensure created_at and updated_at columns are not nullable

Revision ID: 91989d63b5c9
Revises: bb21b4d9a57c
Create Date: 2024-09-17 20:04:01.491694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91989d63b5c9'
down_revision: Union[str, None] = 'bb21b4d9a57c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # List of table names that need the NOT NULL constraint
    tables_with_timestamps = [
        'users', 'activity', 'queries', 'responses', 'user_types'
    ]

    # Schema names for corresponding tables
    schema_names = [
        'entities', 'logs', 'logs', 'logs', 'meta'
    ]

    # Alter each table to set the created_at and updated_at columns as non-nullable
    for table, schema in zip(tables_with_timestamps, schema_names):
        # Ensure there are no NULL values in the columns before adding the NOT NULL constraint
        op.execute(f"""
        UPDATE {schema}.{table}
        SET created_at = NOW()
        WHERE created_at IS NULL;
        """)

        op.execute(f"""
        UPDATE {schema}.{table}
        SET updated_at = NOW()
        WHERE updated_at IS NULL;
        """)

        # Alter columns to set them as non-nullable
        with op.batch_alter_table(table_name=table, schema=schema) as batch_op:
            batch_op.alter_column('created_at', existing_type=sa.DateTime(), nullable=False)
            batch_op.alter_column('updated_at', existing_type=sa.DateTime(), nullable=False)

def downgrade() -> None:
    # List of table names for downgrade to set columns back to nullable
    tables_with_timestamps = [
        'users', 'activity', 'queries', 'responses', 'user_types'
    ]

    # Schema names for corresponding tables
    schema_names = [
        'entities', 'logs', 'logs', 'logs', 'meta'
    ]

    # Alter each table to set the created_at and updated_at columns as nullable
    for table, schema in zip(tables_with_timestamps, schema_names):
        with op.batch_alter_table(table_name=table, schema=schema) as batch_op:
            batch_op.alter_column('created_at', existing_type=sa.DateTime(), nullable=True)
            batch_op.alter_column('updated_at', existing_type=sa.DateTime(), nullable=True)
