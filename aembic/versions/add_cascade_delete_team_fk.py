"""Add cascade delete to team foreign keys

Revision ID: add_cascade_delete_team_fk
Revises: d150a7b7473c
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_cascade_delete_team_fk'
down_revision: Union[str, Sequence[str], None] = 'd150a7b7473c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add CASCADE delete to team foreign keys."""
    # Drop existing foreign key constraints on growth_session
    op.drop_constraint('growth_session_team_id_fkey', 'growth_session', type_='foreignkey')
    
    # Drop existing foreign key constraints on projects
    op.drop_constraint('projects_team_id_fkey', 'projects', type_='foreignkey')
    
    # Recreate with CASCADE delete
    op.create_foreign_key('growth_session_team_id_fkey', 'growth_session', 'team', ['team_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('projects_team_id_fkey', 'projects', 'team', ['team_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema - remove CASCADE delete from team foreign keys."""
    # Drop the CASCADE constraints
    op.drop_constraint('growth_session_team_id_fkey', 'growth_session', type_='foreignkey')
    op.drop_constraint('projects_team_id_fkey', 'projects', type_='foreignkey')
    
    # Recreate without CASCADE delete
    op.create_foreign_key('growth_session_team_id_fkey', 'growth_session', 'team', ['team_id'], ['id'])
    op.create_foreign_key('projects_team_id_fkey', 'projects', 'team', ['team_id'], ['id'])
