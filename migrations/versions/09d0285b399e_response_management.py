"""Response management

Revision ID: 09d0285b399e
Revises: e7743a2322cb
Create Date: 2024-09-20 16:14:49.220426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09d0285b399e'
down_revision: Union[str, None] = 'e7743a2322cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new response_types table
    op.create_table(
        'response_types',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True, comment="Name of the response type"),
        sa.Column('prompt', sa.String(255), nullable=False, comment="Prompt associated with the response type"),
        sa.Column('about', sa.String(255), nullable=True, comment="Description of the response type"),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Record creation date"),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Record last update date"),
        schema='meta'
    )

    # Add new columns to the queries table
    op.add_column('queries', sa.Column('response_type_id', sa.Integer(), nullable=True, comment="Foreign key to the response type"), schema='logs')
    op.add_column('queries', sa.Column('showcase', sa.Boolean(), nullable=False, server_default='false', comment="Indicates whether the query is marked for showcase"), schema='logs')

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_queries_response_type_id',
        'queries',
        'response_types',
        ['response_type_id'],
        ['id'],
        source_schema='logs',
        referent_schema='meta',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop the foreign key constraint
    op.drop_constraint('fk_queries_response_type_id', 'queries', schema='logs', type_='foreignkey')

    # Remove the new columns from the queries table
    op.drop_column('queries', 'response_type_id', schema='logs')
    op.drop_column('queries', 'showcase', schema='logs')

    # Drop the response_types table
    op.drop_table('response_types', schema='meta')
