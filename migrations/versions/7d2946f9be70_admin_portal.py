"""Admin Portal

Revision ID: 7d2946f9be70
Revises: fd8c753ede7a
Create Date: 2024-09-17 18:40:07.727475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d2946f9be70'
down_revision: Union[str, None] = 'fd8c753ede7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert initial UserType entries
    op.execute("""
        INSERT INTO meta.user_types (name, description, created_at, updated_at)
        VALUES
            ('ADMIN', 'Administrator with full access', NOW(), NOW()),
            ('USER', 'Regular user with standard access', NOW(), NOW()),
            ('VIEWER', 'User with read-only access', NOW(), NOW())
    """)


def downgrade():
    # Delete the inserted UserType entries
    op.execute("""
        DELETE FROM meta.user_types
        WHERE name IN ('ADMIN', 'USER', 'VIEWER')
    """)
