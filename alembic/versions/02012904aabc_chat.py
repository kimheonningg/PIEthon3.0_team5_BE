"""chat

Revision ID: 02012904aabc
Revises: 4fe00024af86
Create Date: 2025-06-28 23:08:21.968892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '02012904aabc'
down_revision: Union[str, None] = '4fe00024af86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('references',
    sa.Column('reference_id', sa.String(length=64), nullable=False),
    sa.Column('reference_type', sa.Enum('NOTES', 'APPOINTMENTS', 'EXAMINATIONS', 'MEDICALHISTORIES', 'LABRESULTS', 'IMAGING', 'EXTERNAL', name='referencetype'), nullable=False),
    sa.Column('internal_id', sa.String(length=50), nullable=True),
    sa.Column('external_url', sa.Text(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('reference_id')
    )
    op.create_table('conversations',
    sa.Column('conversation_id', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.Column('patient_mrn', sa.String(length=50), nullable=False),
    sa.Column('doctor_id', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['doctor_id'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['patient_mrn'], ['patients.patient_mrn'], ),
    sa.PrimaryKeyConstraint('conversation_id')
    )
    op.create_table('messages',
    sa.Column('message_id', sa.String(length=50), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('tool_calls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('conversation_id', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ),
    sa.PrimaryKeyConstraint('message_id')
    )
    op.create_table('message_references',
    sa.Column('message_id', sa.String(length=50), nullable=False),
    sa.Column('reference_id', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['messages.message_id'], ),
    sa.ForeignKeyConstraint(['reference_id'], ['references.reference_id'], ),
    sa.PrimaryKeyConstraint('message_id', 'reference_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('message_references')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('references')
    # ### end Alembic commands ###
