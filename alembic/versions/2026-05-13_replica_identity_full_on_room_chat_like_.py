"""Replica identity full on room chat like to allow room filtering on delete event

Revision ID: dba6b23e5bcd
Revises: 73666ecb5657
Create Date: 2026-05-13 11:03:38.082669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'dba6b23e5bcd'
down_revision: Union[str, Sequence[str], None] = '73666ecb5657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('ALTER TABLE room_chat_likes REPLICA IDENTITY FULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('ALTER TABLE room_chat_likes REPLICA IDENTITY DEFAULT')