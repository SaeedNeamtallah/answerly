"""Platform-owner-only cross-company administration routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database.models import (
    BotIntegration,
    Conversation,
    ConversationMessage,
    Project,
    TelegramCustomer,
    User,
    UserAccountStatus,
)
from backend.security.auth import ROLE_COMPANY_ADMIN, ROLE_PLATFORM_OWNER, require_platform_owner_access
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/admin", tags=["Admin Console"])


class AdminCompanyResponse(BaseModel):
    id: int
    username: str
    role: str
    status: str
    company_name: Optional[str]
    project_count: int
    bot_count: int
    conversation_count: int
    created_at: datetime


class AdminOverviewResponse(BaseModel):
    companies: int
    projects: int
    bot_integrations: int
    conversations: int
    open_conversations: int
    escalated_conversations: int
    messages_last_24h: int


class AdminBotIntegrationResponse(BaseModel):
    id: int
    owner_id: int
    owner_username: Optional[str]
    project_id: int
    name: str
    telegram_username: Optional[str]
    status: str
    last_error: Optional[str]
    created_at: datetime


class AdminConversationResponse(BaseModel):
    id: int
    owner_id: int
    bot_integration_id: int
    project_id: int
    status: str
    needs_human: bool
    last_error: Optional[str]
    last_message_at: Optional[datetime]
    created_at: datetime


class AdminProjectResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class AdminConversationMessageResponse(BaseModel):
    id: int
    owner_id: int
    bot_integration_id: int
    conversation_id: int
    sender_type: str
    text: str
    answer_sources_json: Optional[list[dict[str, Any]]]
    retrieval_metadata_json: Optional[dict[str, Any]]
    created_at: datetime


class AdminStatusReasonRequest(BaseModel):
    reason: str = Field(default="platform_owner_action", min_length=3, max_length=255)
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=10080)


def _status_value(value: object) -> str:
    if isinstance(value, UserAccountStatus):
        return value.value
    return str(value or UserAccountStatus.ACTIVE.value)


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one() or 0)


async def _serialize_company(db: AsyncSession, user: User) -> AdminCompanyResponse:
    return AdminCompanyResponse(
        id=int(user.id),
        username=user.username,
        role=user.role,
        status=_status_value(user.status),
        company_name=user.company_name,
        project_count=await _count(db, select(func.count(Project.id)).where(Project.owner_id == user.id)),
        bot_count=await _count(db, select(func.count(BotIntegration.id)).where(BotIntegration.owner_id == user.id)),
        conversation_count=await _count(db, select(func.count(Conversation.id)).where(Conversation.owner_id == user.id)),
        created_at=user.created_at,
    )


def _serialize_admin_conversation(conversation: Conversation) -> AdminConversationResponse:
    return AdminConversationResponse(
        id=int(conversation.id),
        owner_id=int(conversation.owner_id),
        bot_integration_id=int(conversation.bot_integration_id),
        project_id=int(conversation.project_id),
        status=conversation.status,
        needs_human=bool(conversation.needs_human),
        last_error=conversation.last_error,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
    )


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return AdminOverviewResponse(
        companies=await _count(db, select(func.count(User.id)).where(User.role == ROLE_COMPANY_ADMIN)),
        projects=await _count(db, select(func.count(Project.id))),
        bot_integrations=await _count(db, select(func.count(BotIntegration.id))),
        conversations=await _count(db, select(func.count(Conversation.id))),
        open_conversations=await _count(db, select(func.count(Conversation.id)).where(Conversation.status == "open")),
        escalated_conversations=await _count(db, select(func.count(Conversation.id)).where(Conversation.status == "escalated")),
        messages_last_24h=await _count(db, select(func.count(ConversationMessage.id)).where(ConversationMessage.created_at >= since)),
    )


@router.get("/stats", response_model=AdminOverviewResponse)
async def admin_stats(
    current_user: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    return await admin_overview(current_user, db)


@router.get("/companies", response_model=list[AdminCompanyResponse])
async def list_admin_companies(
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
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
        .where(User.role.in_((ROLE_COMPANY_ADMIN, ROLE_PLATFORM_OWNER, "employee")))
        .group_by(User.id)
        .order_by(User.created_at.desc(), User.id.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        AdminCompanyResponse(
            id=int(user.id),
            username=user.username,
            role=user.role,
            status=_status_value(user.status),
            company_name=user.company_name,
            project_count=int(project_count or 0),
            bot_count=int(bot_count or 0),
            conversation_count=int(conversation_count or 0),
            created_at=user.created_at,
        )
        for user, project_count, bot_count, conversation_count in rows
    ]


@router.get("/companies/{company_id}", response_model=AdminCompanyResponse)
async def get_admin_company(
    company_id: int,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, company_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return await _serialize_company(db, user)


@router.get("/companies/{company_id}/projects", response_model=list[AdminProjectResponse])
async def list_admin_company_projects(
    company_id: int,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == int(company_id))
        .order_by(Project.created_at.desc(), Project.id.desc())
    )
    return [
        AdminProjectResponse(
            id=int(project.id),
            owner_id=int(project.owner_id),
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in result.scalars().all()
    ]


@router.get("/companies/{company_id}/bot-integrations", response_model=list[AdminBotIntegrationResponse])
async def list_admin_company_bot_integrations(
    company_id: int,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BotIntegration, User.username)
        .join(User, User.id == BotIntegration.owner_id)
        .where(BotIntegration.owner_id == int(company_id))
        .order_by(BotIntegration.created_at.desc(), BotIntegration.id.desc())
    )
    return [
        AdminBotIntegrationResponse(
            id=int(bot.id),
            owner_id=int(bot.owner_id),
            owner_username=username,
            project_id=int(bot.project_id),
            name=bot.name,
            telegram_username=bot.telegram_username,
            status=bot.status,
            last_error=bot.last_error,
            created_at=bot.created_at,
        )
        for bot, username in result.all()
    ]


@router.get("/companies/{company_id}/conversations", response_model=list[AdminConversationResponse])
async def list_admin_company_conversations(
    company_id: int,
    status: Optional[str] = None,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Conversation)
        .where(Conversation.owner_id == int(company_id))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
    )
    if status:
        stmt = stmt.where(Conversation.status == status)
    conversations = list((await db.execute(stmt)).scalars().all())
    return [_serialize_admin_conversation(conversation) for conversation in conversations]


@router.get("/bot-integrations", response_model=list[AdminBotIntegrationResponse])
async def list_admin_bot_integrations(
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BotIntegration, User.username)
        .join(User, User.id == BotIntegration.owner_id)
        .order_by(BotIntegration.created_at.desc(), BotIntegration.id.desc())
    )
    return [
        AdminBotIntegrationResponse(
            id=int(bot.id),
            owner_id=int(bot.owner_id),
            owner_username=username,
            project_id=int(bot.project_id),
            name=bot.name,
            telegram_username=bot.telegram_username,
            status=bot.status,
            last_error=bot.last_error,
            created_at=bot.created_at,
        )
        for bot, username in result.all()
    ]


@router.get("/conversations", response_model=list[AdminConversationResponse])
async def list_admin_conversations(
    status: Optional[str] = None,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversation).order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
    if status:
        stmt = stmt.where(Conversation.status == status)
    conversations = list((await db.execute(stmt)).scalars().all())
    return [_serialize_admin_conversation(conversation) for conversation in conversations]


@router.get("/conversations/{conversation_id}", response_model=AdminConversationResponse)
async def get_admin_conversation(
    conversation_id: int,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _serialize_admin_conversation(conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=list[AdminConversationMessageResponse])
async def list_admin_conversation_messages(
    conversation_id: int,
    _: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == int(conversation_id))
        .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
    )
    return [
        AdminConversationMessageResponse(
            id=int(message.id),
            owner_id=int(message.owner_id),
            bot_integration_id=int(message.bot_integration_id),
            conversation_id=int(message.conversation_id),
            sender_type=message.sender_type,
            text=message.text,
            answer_sources_json=message.answer_sources_json,
            retrieval_metadata_json=message.retrieval_metadata_json,
            created_at=message.created_at,
        )
        for message in result.scalars().all()
    ]


@router.post("/companies/{company_id}/activate", response_model=AdminCompanyResponse)
async def activate_company(
    company_id: int,
    current_user: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    user = await auth_service.set_user_status(
        db,
        user_id=company_id,
        status=UserAccountStatus.ACTIVE,
        status_reason="platform_owner_activation",
        status_changed_by=str(current_user.id),
    )
    await db.commit()
    return await _serialize_company(db, user)


@router.post("/companies/{company_id}/suspend", response_model=AdminCompanyResponse)
async def suspend_company(
    company_id: int,
    payload: AdminStatusReasonRequest | None = None,
    current_user: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    reason = payload.reason if payload else "platform_owner_suspension"
    user = await auth_service.set_user_status(
        db,
        user_id=company_id,
        status=UserAccountStatus.SUSPENDED,
        suspension_minutes=payload.duration_minutes if payload else None,
        status_reason=reason,
        status_changed_by=str(current_user.id),
    )
    await db.commit()
    return await _serialize_company(db, user)


@router.post("/companies/{company_id}/block", response_model=AdminCompanyResponse)
async def block_company(
    company_id: int,
    payload: AdminStatusReasonRequest | None = None,
    current_user: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    reason = payload.reason if payload else "platform_owner_block"
    user = await auth_service.set_user_status(
        db,
        user_id=company_id,
        status=UserAccountStatus.BLOCKED,
        status_reason=reason,
        status_changed_by=str(current_user.id),
    )
    await db.commit()
    return await _serialize_company(db, user)
