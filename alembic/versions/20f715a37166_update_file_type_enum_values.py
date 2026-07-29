"""update_file_type_enum_values

Revision ID: 20f715a37166
Revises: bb6b7996064f
Create Date: 2026-07-29 15:21:16.538969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20f715a37166'
down_revision: Union[str, Sequence[str], None] = 'bb6b7996064f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE file_type_enum ADD VALUE IF NOT EXISTS 'CITIZENSHIP_FRONT';")
    op.execute("ALTER TYPE file_type_enum ADD VALUE IF NOT EXISTS 'CITIZENSHIP_BACK';")
    op.execute("ALTER TYPE file_type_enum ADD VALUE IF NOT EXISTS 'PROFILE';")
    op.execute("ALTER TYPE file_type_enum ADD VALUE IF NOT EXISTS 'MISTRI_CERTIFICATE';")
    op.execute("ALTER TYPE file_type_enum ADD VALUE IF NOT EXISTS 'OTHER';")


def downgrade() -> None:
    """Downgrade schema."""
    pass
