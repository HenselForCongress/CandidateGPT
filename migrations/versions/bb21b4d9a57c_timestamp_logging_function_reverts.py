"""Add triggers for updated_at and set default values for created_at and updated_at

Revision ID: bb21b4d9a57c
Revises: d22851a20b16
Create Date: 2024-09-17 19:51:41.388764

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bb21b4d9a57c'
down_revision = 'd22851a20b16'
branch_labels = None
depends_on = None

def upgrade():
    # Create Update Timestamp Function in Meta Schema
    op.execute("""
    CREATE OR REPLACE FUNCTION meta.update_updated_at_column()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$;
    """)

    # List of table names that need the trigger
    tables_with_updated_at = [
        'users', 'activity', 'queries', 'responses', 'user_types'
    ]

    # Schema names for corresponding tables
    schema_names = [
        'entities', 'logs', 'logs', 'logs', 'meta'
    ]

    # For each table, add created_at and updated_at columns if they don't exist,
    # and set default values to NOW()
    for table, schema in zip(tables_with_updated_at, schema_names):
        # Check and add 'created_at' column if it doesn't exist
        op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = 'created_at'
            ) THEN
                ALTER TABLE {schema}.{table} ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL;
            END IF;
        END;
        $$;
        """)

        # Check and add 'updated_at' column if it doesn't exist
        op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE {schema}.{table} ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL;
            END IF;
        END;
        $$;
        """)

    # Creating a trigger for each table
    for table, schema in zip(tables_with_updated_at, schema_names):
        op.execute(f"""
        DROP TRIGGER IF EXISTS update_{table}_updated_at ON {schema}.{table};
        CREATE TRIGGER update_{table}_updated_at BEFORE UPDATE ON {schema}.{table}
        FOR EACH ROW EXECUTE FUNCTION meta.update_updated_at_column();
        """)

def downgrade():
    # List of table names that have the trigger
    tables_with_updated_at = [
        'users', 'activity', 'queries', 'responses', 'user_types'
    ]

    # Schema names for corresponding tables
    schema_names = [
        'entities', 'logs', 'logs', 'logs', 'meta'
    ]

    # Drop the triggers
    for table, schema in zip(tables_with_updated_at, schema_names):
        op.execute(f"""
        DROP TRIGGER IF EXISTS update_{table}_updated_at ON {schema}.{table};
        """)

    # Drop the function
    op.execute("""
    DROP FUNCTION IF EXISTS meta.update_updated_at_column();
    """)

    # Remove the created_at and updated_at columns if they exist
    for table, schema in zip(tables_with_updated_at, schema_names):
        op.execute(f"""
        ALTER TABLE {schema}.{table} DROP COLUMN IF EXISTS created_at;
        ALTER TABLE {schema}.{table} DROP COLUMN IF EXISTS updated_at;
        """)
