"""add birthdate and gender to patient

Revision ID: 639f34a65468
Revises: b8754c7bd2a3
Create Date: 2025-06-28 15:50:02.156551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '639f34a65468'
down_revision: Union[str, None] = 'b8754c7bd2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('patients', sa.Column('birthdate', sa.DateTime(), nullable=False))
    op.add_column('patients', sa.Column('gender', sa.String(length=20), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('patients', 'gender')
    op.drop_column('patients', 'birthdate')
    # ### end Alembic commands ###
