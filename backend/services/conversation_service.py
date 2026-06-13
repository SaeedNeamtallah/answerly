"""Company-scoped durable Telegram conversation workflows."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database.models import (
    BotIntegration,
    Conversation,
    ConversationMessage,
    TelegramCustomer,
)
from backend.security.sanitization import sanitize_text
from backend.services.telegram_api_service import TelegramAPIService
from backend.services.token_crypto_service import TokenCryptoService


CONVERSATION_STATUSES = {"open", "escalated", "resolved", "blocked"}
MESSAGE_SENDER_TYPES = {"customer", "bot", "agent", "system", "error"}


class ConversationError(ValueError):
    """Validation error for conversation operations."""


class ConversationService:
    """Persistence and dashboard workflows for Telegram support conversations."""

    def __init__(
        self,
        crypto_service: TokenCryptoService | None = None,
        telegram_api: TelegramAPIService | None = None,
    ):
        self._crypto_service = crypto_service
        self.telegram_api = telegram_api or TelegramAPIService()

    @property
    def crypto_service(self) -> TokenCryptoService:
        if self._crypto_service is None:
            self._crypto_service = TokenCryptoService()
        return self._crypto_service

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _raw_payload_expiry() -> datetime:
        return ConversationService._now() + timedelta(days=max(1, int(settings.telegram_raw_payload_retention_days)))

    @staticmethod
    def _clean_message_text(value: str) -> str:
        text = sanitize_text(value, max_length=4000, strip_html=True, allow_newlines=True)
        if not text:
            raise ConversationError("Message text is required")
        return text

    async def get_or_create_customer(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        chat_id: str,
        telegram_user: dict[str, Any] | None,
    ) -> TelegramCustomer:
        telegram_user = telegram_user or {}
        chat_id_text = sanitize_text(chat_id, max_length=64, strip_html=True, allow_newlines=False)
        stmt = select(TelegramCustomer).where(
            TelegramCustomer.bot_integration_id == integration.id,
            TelegramCustomer.chat_id == chat_id_text,
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        if customer is None:
            customer = TelegramCustomer(
                owner_id=integration.owner_id,
                bot_integration_id=integration.id,
                chat_id=chat_id_text,
            )

        customer.telegram_user_id = sanitize_text(telegram_user.get("id"), max_length=64, strip_html=True, allow_newlines=False) or None
        customer.username = sanitize_text(telegram_user.get("username"), max_length=120, strip_html=True, allow_newlines=False) or None
        customer.first_name = sanitize_text(telegram_user.get("first_name"), max_length=120, strip_html=True, allow_newlines=False) or None
        customer.last_name = sanitize_text(telegram_user.get("last_name"), max_length=120, strip_html=True, allow_newlines=False) or None
        customer.language_code = sanitize_text(telegram_user.get("language_code"), max_length=16, strip_html=True, allow_newlines=False) or None
        customer.last_seen_at = self._now()
        db.add(customer)
        await db.flush()
        return customer

    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        customer: TelegramCustomer,
    ) -> Conversation:
        stmt = (
            select(Conversation)
            .where(
                Conversation.bot_integration_id == integration.id,
                Conversation.telegram_customer_id == customer.id,
                Conversation.status.in_(("open", "escalated")),
            )
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            conversation = Conversation(
                owner_id=integration.owner_id,
                bot_integration_id=integration.id,
                telegram_customer_id=customer.id,
                project_id=integration.project_id,
                status="open",
            )
            db.add(conversation)
            await db.flush()
        return conversation

    async def find_existing_customer_message(
        self,
        db: AsyncSession,
        *,
        integration_id: int,
        customer_id: int,
        telegram_update_id: str | None,
        telegram_message_id: str | None,
    ) -> ConversationMessage | None:
        stmt = select(ConversationMessage).where(ConversationMessage.bot_integration_id == int(integration_id))
        if telegram_update_id:
            stmt = stmt.where(ConversationMessage.telegram_update_id == str(telegram_update_id))
        elif telegram_message_id:
            stmt = stmt.where(
                ConversationMessage.telegram_customer_id == int(customer_id),
                ConversationMessage.telegram_message_id == str(telegram_message_id),
            )
        else:
            return None
        result = await db.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def save_message(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        conversation: Conversation,
        sender_type: str,
        text: str,
        delivery_status: str = "none",
        customer: TelegramCustomer | None = None,
        agent_user_id: int | None = None,
        telegram_update_id: str | None = None,
        telegram_message_id: str | None = None,
        answer_sources: list[dict[str, Any]] | None = None,
        retrieval_metadata: dict[str, Any] | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> tuple[ConversationMessage, bool]:
        if sender_type not in MESSAGE_SENDER_TYPES:
            raise ConversationError("Unsupported message sender type")

        if sender_type == "customer":
            existing = await self.find_existing_customer_message(
                db,
                integration_id=integration.id,
                customer_id=int(customer.id) if customer else 0,
                telegram_update_id=telegram_update_id,
                telegram_message_id=telegram_message_id,
            )
            if existing is not None:
                return existing, False

        message = ConversationMessage(
            owner_id=integration.owner_id,
            bot_integration_id=integration.id,
            conversation_id=conversation.id,
            telegram_customer_id=customer.id if customer else conversation.telegram_customer_id,
            sender_type=sender_type,
            agent_user_id=agent_user_id,
            text=self._clean_message_text(text),
            telegram_update_id=str(telegram_update_id) if telegram_update_id is not None else None,
            telegram_message_id=str(telegram_message_id) if telegram_message_id is not None else None,
            answer_sources_json=answer_sources,
            retrieval_metadata_json=retrieval_metadata,
            raw_payload_json=raw_payload,
            raw_payload_expires_at=self._raw_payload_expiry() if raw_payload is not None else None,
            delivery_status=delivery_status,
        )
        conversation.last_message_at = self._now()
        if sender_type == "error":
            conversation.last_error = message.text[:1000]
        db.add(message)
        db.add(conversation)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            existing = await self.find_existing_customer_message(
                db,
                integration_id=integration.id,
                customer_id=int(customer.id) if customer else 0,
                telegram_update_id=telegram_update_id,
                telegram_message_id=telegram_message_id,
            )
            if existing is not None:
                return existing, False
            raise
        return message, True

    async def list_conversations(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        status: str | None = None,
        needs_human: bool | None = None,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.customer),
                selectinload(Conversation.bot_integration),
                selectinload(Conversation.assigned_to_user),
            )
            .where(Conversation.owner_id == int(owner_id))
        )
        if status:
            stmt = stmt.where(Conversation.status == status)
        if needs_human is not None:
            stmt = stmt.where(Conversation.needs_human == bool(needs_human))
        result = await db.execute(stmt.order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc()))
        return list(result.scalars().all())

    async def get_conversation(self, db: AsyncSession, *, owner_id: int, conversation_id: int) -> Conversation | None:
        result = await db.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.customer),
                selectinload(Conversation.bot_integration),
                selectinload(Conversation.assigned_to_user),
            )
            .where(Conversation.id == int(conversation_id), Conversation.owner_id == int(owner_id))
        )
        return result.scalar_one_or_none()

    async def list_messages(self, db: AsyncSession, *, owner_id: int, conversation_id: int) -> list[ConversationMessage]:
        conversation = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        if conversation is None:
            raise ConversationError("Conversation not found")
        result = await db.execute(
            select(ConversationMessage)
            .where(
                ConversationMessage.owner_id == int(owner_id),
                ConversationMessage.conversation_id == int(conversation_id),
            )
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        )
        return list(result.scalars().all())

    async def set_status(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        conversation_id: int,
        status: str,
        needs_human: bool | None = None,
    ) -> Conversation:
        if status not in CONVERSATION_STATUSES:
            raise ConversationError("Unsupported conversation status")
        conversation = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        if conversation is None:
            raise ConversationError("Conversation not found")
        conversation.status = status
        if needs_human is not None:
            conversation.needs_human = bool(needs_human)
        db.add(conversation)
        await db.commit()
        refreshed = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        return refreshed or conversation

    async def assign_to_self(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        conversation_id: int,
        user_id: int,
    ) -> Conversation:
        conversation = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        if conversation is None:
            raise ConversationError("Conversation not found")
        conversation.assigned_to_user_id = int(user_id)
        conversation.needs_human = True
        db.add(conversation)
        await db.commit()
        refreshed = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        return refreshed or conversation

    async def block_customer(self, db: AsyncSession, *, owner_id: int, conversation_id: int) -> Conversation:
        conversation = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        if conversation is None:
            raise ConversationError("Conversation not found")
        customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
        if customer is not None and customer.owner_id == int(owner_id):
            customer.is_blocked = True
            db.add(customer)
        conversation.status = "blocked"
        conversation.needs_human = False
        db.add(conversation)
        await db.commit()
        refreshed = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        return refreshed or conversation

    async def manual_reply(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        conversation_id: int,
        agent_user_id: int,
        text: str,
    ) -> ConversationMessage:
        conversation = await self.get_conversation(db, owner_id=owner_id, conversation_id=conversation_id)
        if conversation is None:
            raise ConversationError("Conversation not found")
        integration = await db.get(BotIntegration, conversation.bot_integration_id)
        customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
        if integration is None or customer is None or integration.owner_id != int(owner_id):
            raise ConversationError("Conversation integration is unavailable")
        token = self.crypto_service.decrypt_token(integration.token_encrypted)
        result = await self.telegram_api.send_message(token, customer.chat_id, self._clean_message_text(text))
        telegram_message_id = result.get("message_id")
        message, _ = await self.save_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="agent",
            agent_user_id=agent_user_id,
            text=text,
            telegram_message_id=str(telegram_message_id) if telegram_message_id is not None else None,
        )
        await db.commit()
        await db.refresh(message)
        return message
