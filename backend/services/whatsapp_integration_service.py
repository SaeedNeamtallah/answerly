import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exc

from backend.database.models import WhatsAppIntegration
import uuid

logger = logging.getLogger(__name__)

class WhatsAppIntegrationError(Exception):
    pass

_ALLOWED_STATUSES = {
    "pending",
    "initializing",
    "qr_ready",
    "connected",
    "disconnected",
    "expired",
    "error",
    "unknown",
}


def _normalize_status(status: str) -> str:
    clean = str(status or "").strip().lower()
    if clean not in _ALLOWED_STATUSES:
        return "unknown"
    return clean


class WhatsAppIntegrationService:
    async def list_integrations(self, db: AsyncSession, owner_id: int) -> list[WhatsAppIntegration]:
        query = select(WhatsAppIntegration).where(WhatsAppIntegration.owner_id == owner_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_integration(self, db: AsyncSession, owner_id: int, integration_id: int) -> Optional[WhatsAppIntegration]:
        query = select(WhatsAppIntegration).where(
            WhatsAppIntegration.owner_id == owner_id,
            WhatsAppIntegration.id == integration_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_integration_by_session_id(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Optional[WhatsAppIntegration]:
        query = select(WhatsAppIntegration).where(WhatsAppIntegration.session_id == session_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_integration(
        self,
        db: AsyncSession,
        owner_id: int,
        project_id: int,
        name: str,
        phone_number: Optional[str] = None,
        show_sources_to_customer: bool = False,
        human_handoff_enabled: bool = True,
        fallback_message: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> WhatsAppIntegration:
        session_id = str(uuid.uuid4())
        integration = WhatsAppIntegration(
            owner_id=owner_id,
            project_id=project_id,
            name=name,
            phone_number=phone_number,
            session_id=session_id,
            status="pending",
            show_sources_to_customer=show_sources_to_customer,
            human_handoff_enabled=human_handoff_enabled,
            fallback_message=fallback_message,
            system_prompt=system_prompt,
        )
        db.add(integration)
        try:
            await db.commit()
            await db.refresh(integration)
            return integration
        except exc.IntegrityError as e:
            await db.rollback()
            logger.exception("Failed to create whatsapp integration")
            raise WhatsAppIntegrationError("Invalid data or constraints violated") from e

    async def update_integration(
        self,
        db: AsyncSession,
        owner_id: int,
        integration_id: int,
        project_id: Optional[int] = None,
        name: Optional[str] = None,
        show_sources_to_customer: Optional[bool] = None,
        human_handoff_enabled: Optional[bool] = None,
        fallback_message: Optional[str] = None,
        system_prompt: Optional[str] = None,
        fallback_message_provided: bool = False,
        system_prompt_provided: bool = False,
    ) -> WhatsAppIntegration:
        integration = await self.get_integration(db, owner_id, integration_id)
        if not integration:
            raise WhatsAppIntegrationError("WhatsApp integration not found")

        if project_id is not None:
            integration.project_id = project_id
        if name is not None:
            integration.name = name
        if show_sources_to_customer is not None:
            integration.show_sources_to_customer = show_sources_to_customer
        if human_handoff_enabled is not None:
            integration.human_handoff_enabled = human_handoff_enabled
        if fallback_message_provided:
            integration.fallback_message = fallback_message
        if system_prompt_provided:
            integration.system_prompt = system_prompt

        try:
            await db.commit()
            await db.refresh(integration)
            return integration
        except exc.IntegrityError as e:
            await db.rollback()
            logger.exception("Failed to update whatsapp integration")
            raise WhatsAppIntegrationError("Update failed") from e

    async def update_status(
        self,
        db: AsyncSession,
        integration: WhatsAppIntegration,
        status: str,
        last_error: Optional[str] = None,
    ) -> WhatsAppIntegration:
        normalized_status = _normalize_status(status)
        integration.status = normalized_status
        integration.last_update_at = datetime.now(timezone.utc)
        if normalized_status in {"connected", "initializing", "qr_ready"}:
            integration.last_error = None
        elif last_error is not None:
            integration.last_error = str(last_error)[:1000]

        await db.commit()
        await db.refresh(integration)
        return integration

    async def update_status_by_session_id(
        self,
        db: AsyncSession,
        session_id: str,
        status: str,
        last_error: Optional[str] = None,
    ) -> WhatsAppIntegration:
        integration = await self.get_integration_by_session_id(db, session_id)
        if not integration:
            raise WhatsAppIntegrationError("WhatsApp integration not found")
        return await self.update_status(
            db,
            integration=integration,
            status=status,
            last_error=last_error,
        )

    async def delete_integration(self, db: AsyncSession, owner_id: int, integration_id: int) -> None:
        integration = await self.get_integration(db, owner_id, integration_id)
        if not integration:
            raise WhatsAppIntegrationError("WhatsApp integration not found")
        await db.delete(integration)
        await db.commit()
