"""add_hybrid_fields_to_messages

Revision ID: 6fa172fbbec3
Revises: 
Create Date: 2026-05-01 18:49:39.630836

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6fa172fbbec3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Create users table ──────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # ── Create conversations table ──────────────────────────────────
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False),
        sa.Column('user1_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user2_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'],
                    unique=False)

    # ── Create messages table ───────────────────────────────────────
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'),
                  nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('client_message_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['sender_id'],   ['users.id']),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_id', 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_client_message_id'), 'messages',
                    ['client_message_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_messages_client_message_id'),
                  table_name='messages')
    op.drop_index('ix_messages_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_conversations_id', table_name='conversations')
    op.drop_table('conversations')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')