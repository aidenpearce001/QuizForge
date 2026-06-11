"""add for_exam to questions and session_type to sessions

Revision ID: b497a65e44f4
Revises: ff576bcf9faf
Create Date: 2026-05-06 13:44:58.091005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b497a65e44f4'
down_revision: Union[str, None] = 'ff576bcf9faf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('for_exam', sa.Boolean(), nullable=False, server_default=sa.false()))
    session_type_enum = sa.Enum('normal', 'exam', name='session_type_enum')
    session_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('sessions', sa.Column('session_type', session_type_enum, nullable=False, server_default='normal'))


def downgrade() -> None:
    op.drop_column('sessions', 'session_type')
    op.drop_column('questions', 'for_exam')
    op.execute("DROP TYPE IF EXISTS session_type_enum")
