"""Platform-owner admin service helpers for cross-company workflows."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    BotIntegration,
    Conversation,
    ConversationMessage,
    Project,
    User,
    UserAccountStatus,
)
from backend.security.auth import ROLE_COMPANY_ADMIN
from backend.services.auth_service import AuthService

class AdminService:
    """Queries and account-state actions used by platform-owner routes."""

    @staticmethod
    async def _count(db: AsyncSession, stmt) -> int:
        return int((await db.execute(stmt)).scalar_one() or 0)

    async def overview(self, db: AsyncSession) -> dict[str, int]:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        return {
            "companies": await self._count(db, select(func.count(User.id)).where(User.role == ROLE_COMPANY_ADMIN)),
            "projects": await self._count(db, select(func.count(Project.id))),
            "bot_integrations": await self._count(db, select(func.count(BotIntegration.id))),
            "conversations": await self._count(db, select(func.count(Conversation.id))),
            "open_conversations": await self._count(
                db,
                select(func.count(Conversation.id)).where(Conversation.status == "open"),
            ),
            "escalated_conversations": await self._count(
                db,
                select(func.count(Conversation.id)).where(Conversation.status == "escalated"),
            ),
            "messages_last_24h": await self._count(
                db,
                select(func.count(ConversationMessage.id)).where(ConversationMessage.created_at >= since),
            ),
        }

    async def list_companies(self, db: AsyncSession) -> list[tuple[User, int, int, int]]:
        stmt = (
            select(
                User,
                func.count(func.distinct(Project.id)).label("project_count"),
                func.count(func.distinct(BotIntegration.id)).label("bot_count"),
                func.count(func.distinct(Conversation.id)).label("conversation_count"),
            )
            .outerjoin(Project, Project.owner_id == User.id)
            .outerjoin(BotIntegration, BotIntegration.owner_id == User.id)
            .outerjoin(Conversation, Conversation.owner_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc(), User.id.desc())
        )
        return list((await db.execute(stmt)).all())

    async def get_company(self, db: AsyncSession, *, company_id: int) -> User | None:
        return await db.get(User, int(company_id))

    async def list_company_projects(self, db: AsyncSession, *, company_id: int) -> list[Project]:
        result = await db.execute(
            select(Project)
            .where(Project.owner_id == int(company_id))
            .order_by(Project.created_at.desc(), Project.id.desc())
        )
        return list(result.scalars().all())

    async def list_company_bot_integrations(self, db: AsyncSession, *, company_id: int) -> list[BotIntegration]:
        result = await db.execute(
            select(BotIntegration)
            .where(BotIntegration.owner_id == int(company_id))
            .order_by(BotIntegration.created_at.desc(), BotIntegration.id.desc())
        )
        return list(result.scalars().all())

    async def list_company_conversations(
        self,
        db: AsyncSession,
        *,
        company_id: int,
        status: str | None = None,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.owner_id == int(company_id))
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
        )
        if status:
            stmt = stmt.where(Conversation.status == status)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def set_company_status(
        self,
        db: AsyncSession,
        *,
        company_id: int,
        status: UserAccountStatus,
        actor_id: int,
        reason: str,
        duration_minutes: int | None = None,
        auth_service: AuthService | None = None,
    ) -> User:
        resolved_auth_service = auth_service or AuthService()
        return await resolved_auth_service.set_user_status(
            db,
            user_id=int(company_id),
            status=status,
            suspension_minutes=duration_minutes,
            status_reason=reason,
            status_changed_by=str(actor_id),
        )

    async def list_conversation_messages(self, db: AsyncSession, *, conversation_id: int) -> list[ConversationMessage]:
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == int(conversation_id))
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        )
        return list(result.scalars().all())

