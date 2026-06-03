"""add_experience_points_and_level_to_user_profiles

Revision ID: cda0ba820fdc
Revises: 37f0b8c56d5c
Create Date: 2026-06-03 13:28:45.559091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cda0ba820fdc'
down_revision: Union[str, None] = '37f0b8c56d5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('experience_points', sa.Integer(), nullable=True))
    op.add_column('user_profiles', sa.Column('level', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'level')
    op.drop_column('user_profiles', 'experience_points')
