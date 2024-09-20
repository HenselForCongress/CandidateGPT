"""Load initial data into response_types

Revision ID: 20edf329dd04
Revises: 09d0285b399e
Create Date: 2024-09-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = '20edf329dd04'
down_revision = '09d0285b399e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create an ad-hoc table to use for data insertion.
    response_types_table = table('response_types',
                                 column('name', sa.String),
                                 column('prompt', sa.String),
                                 column('about', sa.String),
                                 schema='meta')

    # Define initial data for response types
    initial_data = [
        {"name": "1 Minute", "prompt": "Provide a response that would take about 1 minute to speak aloud.", "about": "A 1-minute spoken response with inference."},
        {"name": "30 Seconds", "prompt": "Provide a response that would take about 30 seconds to speak aloud.", "about": "A 30-second concise spoken response."},
        {"name": "Concise", "prompt": "Provide a concise response in no more than two sentences, excluding any unnecessary information.", "about": "The most direct answer possible."},
        {"name": "Detailed", "prompt": "Provide a detailed and comprehensive response.", "about": "An in-depth and thorough answer."},
        {"name": "Speculative", "prompt": "Provide a concise response based on the provided information, and include any reasonable inferences or assumptions.", "about": "Includes reasonable inferences and assumptions."},
        {"name": "No Inference", "prompt": "Provide a response based strictly on the provided data without any inferences. If the answer is not found, state that directly.", "about": "Strictly based on data, no inferences."}
    ]

    # Insert data into response_types table
    op.bulk_insert(response_types_table, initial_data)


def downgrade() -> None:
    # Assuming there won't be any other entries in response_types, we can truncate it.
    op.execute('TRUNCATE TABLE meta.response_types CASCADE')
