"""Add cascade deletes for ActionItem SessionNote and TeamMember

Revision ID: 3c4f9571e99a
Revises: add_cascade_delete_team_fk
Create Date: 2026-02-22 06:48:04.065976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4f9571e99a'
down_revision: Union[str, Sequence[str], None] = 'add_cascade_delete_team_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
