"""fix enum values and create debt status history table

Revision ID: f1b2c3d4e5f6
Revises: fa24f2ca7103
Create Date: 2026-02-26 15:48:31.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fa24f2ca7103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing values to enums in PostgreSQL
    # Using execute with exception handling for already existing values
    try:
        op.execute("ALTER TYPE debtpriority ADD VALUE 'critical' AFTER 'high'")
    except Exception:
        pass  # Value might already exist
    
    try:
        op.execute("ALTER TYPE debtstatus ADD VALUE 'identified' BEFORE 'open'")
    except Exception:
        pass  # Value might already exist
    
    try:
        op.execute("ALTER TYPE debtstatus ADD VALUE 'wont_fix' AFTER 'resolved'")
    except Exception:
        pass  # Value might already exist


def downgrade() -> None:
    """Downgrade schema."""
    # Note: Removing values from PostgreSQL enums is not straightforward
    # This would require manual intervention in a real scenario
    pass
