"""Webhook orchestration for database-backed WhatsApp bot integrations."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import WhatsAppIntegration
from backend.services.whatsapp_integration_service import WhatsAppIntegrationService
from backend.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

class WhatsAppWebhookError(ValueError):
    """Sanitized webhook processing failure."""

class WhatsAppWebhookService:
    def __init__(
        self,
        integration_service: WhatsAppIntegrationService | None = None,
        conversation_service: ConversationService | None = None,
    ):
        self.integration_service = integration_service or WhatsAppIntegrationService()
        self.conversation_service = conversation_service or ConversationService()

    @staticmethod
    def _enqueue_reply_generation(customer_message_id: int) -> None:
        from backend.tasks.whatsapp_query import generate_whatsapp_reply_task
        generate_whatsapp_reply_task.delay(int(customer_message_id))

    async def handle_update(
        self,
        db: AsyncSession,
        *,
        integration_id: int,
        update: dict[str, Any],
    ) -> dict[str, Any]:
        from backend.database.models import WhatsAppIntegration
        integration = await db.get(WhatsAppIntegration, integration_id)
        if integration is None:
            raise WhatsAppWebhookError("WhatsApp integration not found")

        if integration.status not in {"active", "connected", "error"}:
            return {"ok": True, "ignored": True, "reason": "integration_disabled"}

        text = update.get("text")
        if not text:
            return {"ok": True, "ignored": True, "reason": "non_text_message"}

        remote_jid = update.get("remoteJid")
        if not remote_jid:
            return {"ok": True, "ignored": True, "reason": "missing_remote_jid"}

        phone_number = str(remote_jid)
        push_name = update.get("pushName")
        message_id = update.get("messageId")

        customer = await self.conversation_service.get_or_create_whatsapp_customer(
            db,
            integration=integration,
            phone_number=phone_number,
            name=push_name,
        )

        conversation = await self.conversation_service.get_or_create_whatsapp_conversation(
            db,
            integration=integration,
            customer=customer,
        )


        customer_message, created = await self.conversation_service.save_whatsapp_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="customer",
            text=text,
            whatsapp_message_id=str(message_id) if message_id else None,
            raw_payload=update,
            retrieval_metadata={"reply_generation_status": "queued"},
        )
        if not created:
            await db.commit()
            return {"success": True, "reason": "idempotent_skip"}

        try:
            await db.commit()
            self._enqueue_reply_generation(int(customer_message.id))
        except Exception as exc:
            raise WhatsAppWebhookError("WhatsApp reply queue is unavailable") from exc

        result = {"ok": True, "conversation_id": conversation.id, "reply_queued": True}
        if not created:
            result["duplicate"] = True
            result["message_id"] = customer_message.id
        return result
