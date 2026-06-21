"""Add WhatsApp integration models

Revision ID: b4a93309a816
Revises: 20260619_01
Create Date: 2026-06-20 09:04:24.558529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4a93309a816'
down_revision: Union[str, None] = '20260619_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create whatsapp_integrations
    op.create_table(
        'whatsapp_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('phone_number', sa.String(length=64), nullable=True),
        sa.Column('session_id', sa.String(length=120), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending', nullable=False),
        sa.Column('show_sources_to_customer', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('human_handoff_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('fallback_message', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_update_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_integrations_id'), 'whatsapp_integrations', ['id'], unique=False)
    op.create_index('ix_whatsapp_integrations_owner_project', 'whatsapp_integrations', ['owner_id', 'project_id'], unique=False)
    op.create_index('ix_whatsapp_integrations_owner_status', 'whatsapp_integrations', ['owner_id', 'status'], unique=False)
    op.create_index(op.f('ix_whatsapp_integrations_phone_number'), 'whatsapp_integrations', ['phone_number'], unique=False)
    op.create_index(op.f('ix_whatsapp_integrations_session_id'), 'whatsapp_integrations', ['session_id'], unique=True)
    op.create_index(op.f('ix_whatsapp_integrations_status'), 'whatsapp_integrations', ['status'], unique=False)

    # Create whatsapp_customers
    op.create_table(
        'whatsapp_customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('whatsapp_integration_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['whatsapp_integration_id'], ['whatsapp_integrations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_customers_id'), 'whatsapp_customers', ['id'], unique=False)
    op.create_index('ix_whatsapp_customers_integration_phone', 'whatsapp_customers', ['whatsapp_integration_id', 'phone_number'], unique=True)
    op.create_index('ix_whatsapp_customers_owner_integration', 'whatsapp_customers', ['owner_id', 'whatsapp_integration_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_customers_phone_number'), 'whatsapp_customers', ['phone_number'], unique=False)

    # Update conversations
    op.add_column('conversations', sa.Column('channel', sa.String(length=32), server_default='telegram', nullable=False))
    op.add_column('conversations', sa.Column('whatsapp_integration_id', sa.Integer(), nullable=True))
    op.add_column('conversations', sa.Column('whatsapp_customer_id', sa.Integer(), nullable=True))
    op.alter_column('conversations', 'bot_integration_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('conversations', 'telegram_customer_id', existing_type=sa.Integer(), nullable=True)
    op.create_index(op.f('ix_conversations_channel'), 'conversations', ['channel'], unique=False)
    op.create_index(op.f('ix_conversations_whatsapp_customer_id'), 'conversations', ['whatsapp_customer_id'], unique=False)
    op.create_index(op.f('ix_conversations_whatsapp_integration_id'), 'conversations', ['whatsapp_integration_id'], unique=False)
    op.create_foreign_key(None, 'conversations', 'whatsapp_integrations', ['whatsapp_integration_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'conversations', 'whatsapp_customers', ['whatsapp_customer_id'], ['id'], ondelete='CASCADE')

    # Update conversation_messages
    op.add_column('conversation_messages', sa.Column('whatsapp_integration_id', sa.Integer(), nullable=True))
    op.add_column('conversation_messages', sa.Column('whatsapp_customer_id', sa.Integer(), nullable=True))
    op.add_column('conversation_messages', sa.Column('whatsapp_message_id', sa.String(length=128), nullable=True))
    op.alter_column('conversation_messages', 'bot_integration_id', existing_type=sa.Integer(), nullable=True)
    op.create_index(op.f('ix_conversation_messages_whatsapp_customer_id'), 'conversation_messages', ['whatsapp_customer_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_whatsapp_integration_id'), 'conversation_messages', ['whatsapp_integration_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_whatsapp_message_id'), 'conversation_messages', ['whatsapp_message_id'], unique=False)
    op.create_foreign_key(None, 'conversation_messages', 'whatsapp_customers', ['whatsapp_customer_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'conversation_messages', 'whatsapp_integrations', ['whatsapp_integration_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Revert conversation_messages
    op.drop_constraint(None, 'conversation_messages', type_='foreignkey')
    op.drop_constraint(None, 'conversation_messages', type_='foreignkey')
    op.drop_index(op.f('ix_conversation_messages_whatsapp_message_id'), table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_whatsapp_integration_id'), table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_whatsapp_customer_id'), table_name='conversation_messages')
    op.alter_column('conversation_messages', 'bot_integration_id', existing_type=sa.Integer(), nullable=False)
    op.drop_column('conversation_messages', 'whatsapp_message_id')
    op.drop_column('conversation_messages', 'whatsapp_customer_id')
    op.drop_column('conversation_messages', 'whatsapp_integration_id')

    # Revert conversations
    op.drop_constraint(None, 'conversations', type_='foreignkey')
    op.drop_constraint(None, 'conversations', type_='foreignkey')
    op.drop_index(op.f('ix_conversations_whatsapp_integration_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_whatsapp_customer_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_channel'), table_name='conversations')
    op.alter_column('conversations', 'telegram_customer_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('conversations', 'bot_integration_id', existing_type=sa.Integer(), nullable=False)
    op.drop_column('conversations', 'whatsapp_customer_id')
    op.drop_column('conversations', 'whatsapp_integration_id')
    op.drop_column('conversations', 'channel')

    # Drop tables
    op.drop_index(op.f('ix_whatsapp_customers_phone_number'), table_name='whatsapp_customers')
    op.drop_index('ix_whatsapp_customers_owner_integration', table_name='whatsapp_customers')
    op.drop_index('ix_whatsapp_customers_integration_phone', table_name='whatsapp_customers')
    op.drop_index(op.f('ix_whatsapp_customers_id'), table_name='whatsapp_customers')
    op.drop_table('whatsapp_customers')

    op.drop_index(op.f('ix_whatsapp_integrations_status'), table_name='whatsapp_integrations')
    op.drop_index(op.f('ix_whatsapp_integrations_session_id'), table_name='whatsapp_integrations')
    op.drop_index(op.f('ix_whatsapp_integrations_phone_number'), table_name='whatsapp_integrations')
    op.drop_index('ix_whatsapp_integrations_owner_status', table_name='whatsapp_integrations')
    op.drop_index('ix_whatsapp_integrations_owner_project', table_name='whatsapp_integrations')
    op.drop_index(op.f('ix_whatsapp_integrations_id'), table_name='whatsapp_integrations')
    op.drop_table('whatsapp_integrations')
