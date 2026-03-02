"""history table

Revision ID: fa24f2ca7103
Revises: 88ce694975a0
Create Date: 2026-02-26 15:50:34.296431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa24f2ca7103'
down_revision: Union[str, Sequence[str], None] = '88ce694975a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration is skipped as the debt_status_history table
    # will be properly created in the next migration
    # The original migration had incorrect assumptions about the table structure
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This migration is a no-op, so downgrade is also a no-op
    pass
