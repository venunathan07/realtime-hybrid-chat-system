"""add_edit_message_and_groups

Revision ID: c3f9a2b8d1e4
Revises: ae5d5e0079d1
Create Date: 2026-05-04 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3f9a2b8d1e4'
down_revision: Union[str, Sequence[str], None] = 'ae5d5e0079d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_edited and edited_at to messages
    op.add_column('messages', sa.Column('is_edited', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('messages', sa.Column('edited_at', sa.DateTime(), nullable=True))

    # Add is_group and name to conversations
    op.add_column('conversations', sa.Column('is_group', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('conversations', sa.Column('name', sa.String(), nullable=True))

    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('group_members')
    op.drop_column('conversations', 'name')
    op.drop_column('conversations', 'is_group')
    op.drop_column('messages', 'edited_at')
    op.drop_column('messages', 'is_edited')