"""Initial migration

Revision ID: fd8c753ede7a
Revises:
Create Date: 2024-09-17 17:14:14.016457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd8c753ede7a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas if they don't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS meta")
    op.execute("CREATE SCHEMA IF NOT EXISTS entities")
    op.execute("CREATE SCHEMA IF NOT EXISTS logs")

    # ### commands auto generated by Alembic - please adjust! ###
    # Create 'user_types' table
    op.create_table('user_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Auto incrementing primary key'),
    sa.Column('name', sa.Enum('ADMIN', 'USER', 'VIEWER', name='usertypeenum'), nullable=False, comment='Name of the user type (e.g., Admin, User, Viewer)'),
    sa.Column('description', sa.String(length=255), nullable=True, comment='Description of the user type'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='Record creation date'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Record last update date'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='meta'
    )

    # Create 'users' table
    op.create_table('users',
    sa.Column('user_id', sa.UUID(), nullable=False, comment='Unique user ID'),
    sa.Column('email', sa.String(length=255), nullable=False, comment="User's email address"),
    sa.Column('password_hash', sa.String(length=128), nullable=False, comment='Hashed password'),
    sa.Column('is_active', sa.Boolean(), nullable=True, comment='Is the user active?'),
    sa.Column('user_type_id', sa.Integer(), nullable=False, comment='Foreign key to the user type'),
    sa.Column('last_login', sa.DateTime(), nullable=True, comment='Last login time'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='Record creation date'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Record last update date'),
    sa.ForeignKeyConstraint(['user_type_id'], ['meta.user_types.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id'),
    schema='entities'
    )
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.create_index('idx_users_email', ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_entities_users_email'), ['email'], unique=True)

    # Create 'activity' table
    op.create_table('activity',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Auto incrementing primary key'),
    sa.Column('activity_type', sa.String(length=50), nullable=False, comment='Type of activity (e.g., login, update)'),
    sa.Column('description', sa.Text(), nullable=False, comment='Detailed description of the activity'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of the user who performed the activity'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='Record creation date'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Record last update date'),
    sa.ForeignKeyConstraint(['user_id'], ['entities.users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='logs'
    )

    # Create 'queries' table
    op.create_table('queries',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Auto incrementing primary key'),
    sa.Column('query_text', sa.Text(), nullable=False, comment='Text of the query made by the user'),
    sa.Column('response_text', sa.Text(), nullable=False, comment='Response text for the query'),
    sa.Column('settings_selected', sa.String(length=255), nullable=True, comment='Settings used when making the query'),
    sa.Column('timestamp', sa.DateTime(), nullable=True, comment='Time when query was made'),
    sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP address from which the query was made'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of the user who made the query'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='Record creation date'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Record last update date'),
    sa.ForeignKeyConstraint(['user_id'], ['entities.users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='logs'
    )

    # Create 'responses' table
    op.create_table('responses',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Auto incrementing primary key'),
    sa.Column('response_text', sa.Text(), nullable=False, comment='Response text'),
    sa.Column('query_id', sa.Integer(), nullable=False, comment='Associated query ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='Record creation date'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='Record last update date'),
    sa.ForeignKeyConstraint(['query_id'], ['logs.queries.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='logs'
    )
    # ### end Alembic commands ###

    # Create function to update 'updated_at' column
    op.execute("""
    CREATE OR REPLACE FUNCTION meta.update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # List of tables and their schemas that need the trigger
    tables_with_updated_at = [
        ('user_types', 'meta'),
        ('users', 'entities'),
        ('activity', 'logs'),
        ('queries', 'logs'),
        ('responses', 'logs')
    ]

    # Create triggers for each table
    for table_name, schema_name in tables_with_updated_at:
        op.execute(f"""
        CREATE TRIGGER update_{table_name}_updated_at
        BEFORE UPDATE ON {schema_name}.{table_name}
        FOR EACH ROW EXECUTE FUNCTION meta.update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers from tables
    tables_with_updated_at = [
        ('user_types', 'meta'),
        ('users', 'entities'),
        ('activity', 'logs'),
        ('queries', 'logs'),
        ('responses', 'logs')
    ]

    for table_name, schema_name in tables_with_updated_at:
        op.execute(f"""
        DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {schema_name}.{table_name};
        """)

    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS meta.update_updated_at_column();")

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('responses', schema='logs')
    op.drop_table('queries', schema='logs')
    op.drop_table('activity', schema='logs')
    with op.batch_alter_table('users', schema='entities') as batch_op:
        batch_op.drop_index(batch_op.f('ix_entities_users_email'))
        batch_op.drop_index('idx_users_email')

    op.drop_table('users', schema='entities')
    op.drop_table('user_types', schema='meta')
    # ### end Alembic commands ###

    # Drop schemas
    op.execute("DROP SCHEMA IF EXISTS logs CASCADE")
    op.execute("DROP SCHEMA IF EXISTS entities CASCADE")
    op.execute("DROP SCHEMA IF EXISTS meta CASCADE")
