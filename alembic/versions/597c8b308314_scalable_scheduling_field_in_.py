"""Scalable scheduling field in professional profile

Revision ID: 597c8b308314
Revises: 829818b1b02e
Create Date: 2026-08-01 20:35:44.415831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '597c8b308314'
down_revision: Union[str, Sequence[str], None] = '829818b1b02e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop foreign key constraint on professional_skills that depends on professional_profiles.id
    op.drop_constraint('professional_skills_professional_profile_id_fkey', 'professional_skills', type_='foreignkey')

    # 2. Add new columns to professional_profiles
    op.add_column('professional_profiles', sa.Column('professional_profile_id', sa.String(length=13), nullable=False))
    op.add_column('professional_profiles', sa.Column('work_start_time', sa.Time(), nullable=True))
    op.add_column('professional_profiles', sa.Column('work_end_time', sa.Time(), nullable=True))
    op.add_column('professional_profiles', sa.Column('buffer_between_bookings_minutes', sa.Integer(), nullable=False))
    op.add_column('professional_profiles', sa.Column('max_advance_booking_days', sa.Integer(), nullable=False))
    op.add_column('professional_profiles', sa.Column('min_advance_booking_minutes', sa.Integer(), nullable=False))

    # 3. Drop index and old PK column 'id' from professional_profiles
    op.drop_index(op.f('ix_professional_profiles_id'), table_name='professional_profiles')
    op.drop_column('professional_profiles', 'id')

    # 4. Set professional_profile_id as primary key and create index for professional_profiles
    op.create_primary_key('professional_profiles_pkey', 'professional_profiles', ['professional_profile_id'])
    op.create_index(op.f('ix_professional_profiles_professional_profile_id'), 'professional_profiles', ['professional_profile_id'], unique=False)

    # 5. Alter column type in professional_skills
    op.alter_column('professional_skills', 'professional_profile_id',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=13),
               existing_nullable=False)

    # 6. Re-create foreign key constraint on professional_skills referencing new PK
    op.create_foreign_key('professional_skills_professional_profile_id_fkey', 'professional_skills', 'professional_profiles', ['professional_profile_id'], ['professional_profile_id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop new foreign key constraint on professional_skills
    op.drop_constraint('professional_skills_professional_profile_id_fkey', 'professional_skills', type_='foreignkey')

    # 2. Alter professional_skills column back to INTEGER
    op.alter_column('professional_skills', 'professional_profile_id',
               existing_type=sa.String(length=13),
               type_=sa.INTEGER(),
               existing_nullable=False)

    # 3. Drop new primary key on professional_profiles
    op.drop_constraint('professional_profiles_pkey', 'professional_profiles', type_='primary')

    # 4. Add 'id' column back, set as primary key and re-index
    op.add_column('professional_profiles', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.create_primary_key('professional_profiles_pkey', 'professional_profiles', ['id'])
    op.create_index(op.f('ix_professional_profiles_id'), 'professional_profiles', ['id'], unique=False)

    # 5. Remove new columns and index from professional_profiles
    op.drop_index(op.f('ix_professional_profiles_professional_profile_id'), table_name='professional_profiles')
    op.drop_column('professional_profiles', 'min_advance_booking_minutes')
    op.drop_column('professional_profiles', 'max_advance_booking_days')
    op.drop_column('professional_profiles', 'buffer_between_bookings_minutes')
    op.drop_column('professional_profiles', 'work_end_time')
    op.drop_column('professional_profiles', 'work_start_time')
    op.drop_column('professional_profiles', 'professional_profile_id')

    # 6. Re-create old foreign key constraint referencing 'id'
    op.create_foreign_key('professional_skills_professional_profile_id_fkey', 'professional_skills', 'professional_profiles', ['professional_profile_id'], ['id'], ondelete='CASCADE')
