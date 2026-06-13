"""Company-scoped conversation dashboard routes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database.models import Conversation, ConversationMessage, User
from backend.security.auth import require_company_dashboard_access
from backend.services.conversation_service import ConversationError, ConversationService
from backend.services.telegram_api_service import TelegramAPIError
from backend.services.token_crypto_service import SecretConfigurationError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["Conversations"])


def get_conversation_service() -> ConversationService:
    return ConversationService()


class ConversationResponse(BaseModel):
    id: int
    owner_id: int
    bot_integration_id: int
    bot_name: Optional[str] = None
    telegram_customer_id: int
    customer_label: str
    project_id: int
    status: str
    needs_human: bool
    assigned_to_user_id: Optional[int]
    assigned_to_username: Optional[str] = None
    last_message_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_type: str
    text: str
    agent_user_id: Optional[int]
    telegram_message_id: Optional[str]
    answer_sources_json: Optional[list[dict[str, Any]]] = None
    retrieval_metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime


class ManualReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=4000)


def _customer_label(conversation: Conversation) -> str:
    customer = getattr(conversation, "customer", None)
    if customer is None:
        return "Telegram customer"
    if customer.username:
        return f"@{customer.username}"
    name = " ".join(part for part in [customer.first_name, customer.last_name] if part)
    return name or f"Chat {customer.chat_id}"


def _serialize_conversation(conversation: Conversation) -> ConversationResponse:
    integration = getattr(conversation, "bot_integration", None)
    assigned_user = getattr(conversation, "assigned_to_user", None)
    return ConversationResponse(
        id=int(conversation.id),
        owner_id=int(conversation.owner_id),
        bot_integration_id=int(conversation.bot_integration_id),
        bot_name=getattr(integration, "name", None),
        telegram_customer_id=int(conversation.telegram_customer_id),
        customer_label=_customer_label(conversation),
        project_id=int(conversation.project_id),
        status=str(conversation.status),
        needs_human=bool(conversation.needs_human),
        assigned_to_user_id=conversation.assigned_to_user_id,
        assigned_to_username=getattr(assigned_user, "username", None),
        last_message_at=conversation.last_message_at,
        last_error=conversation.last_error,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _serialize_message(message: ConversationMessage) -> ConversationMessageResponse:
    return ConversationMessageResponse(
        id=int(message.id),
        conversation_id=int(message.conversation_id),
        sender_type=str(message.sender_type),
        text=str(message.text),
        agent_user_id=message.agent_user_id,
        telegram_message_id=message.telegram_message_id,
        answer_sources_json=message.answer_sources_json,
        retrieval_metadata_json=message.retrieval_metadata_json,
        created_at=message.created_at,
    )


def _map_conversation_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SecretConfigurationError):
        return HTTPException(status_code=503, detail="Bot token encryption is not configured")
    if isinstance(exc, TelegramAPIError):
        return HTTPException(status_code=502, detail="Telegram delivery failed")
    if isinstance(exc, ConversationError):
        status_code = 404 if "not found" in str(exc).lower() else 400
        return HTTPException(status_code=status_code, detail=str(exc))
    logger.exception("Unexpected conversation error")
    return HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    status: Optional[str] = None,
    needs_human: Optional[bool] = None,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversations = await service.list_conversations(
            db,
            owner_id=current_user.id,
            status=status,
            needs_human=needs_human,
        )
        return [_serialize_conversation(conversation) for conversation in conversations]
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversation = await service.get_conversation(db, owner_id=current_user.id, conversation_id=conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return _serialize_conversation(conversation)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessageResponse])
async def list_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        messages = await service.list_messages(db, owner_id=current_user.id, conversation_id=conversation_id)
        return [_serialize_message(message) for message in messages]
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.post("/{conversation_id}/reply", response_model=ConversationMessageResponse)
async def manual_reply(
    conversation_id: int,
    payload: ManualReplyRequest,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        message = await service.manual_reply(
            db,
            owner_id=current_user.id,
            conversation_id=conversation_id,
            agent_user_id=getattr(current_user, "employee_id", current_user.id),
            text=payload.text,
        )
        return _serialize_message(message)
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.post("/{conversation_id}/assign-self", response_model=ConversationResponse)
@router.post("/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation_to_self(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversation = await service.assign_to_self(
            db,
            owner_id=current_user.id,
            conversation_id=conversation_id,
            user_id=getattr(current_user, "employee_id", current_user.id),
        )
        return _serialize_conversation(conversation)
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.post("/{conversation_id}/escalate", response_model=ConversationResponse)
async def escalate_conversation(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversation = await service.set_status(
            db,
            owner_id=current_user.id,
            conversation_id=conversation_id,
            status="escalated",
            needs_human=True,
        )
        return _serialize_conversation(conversation)
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.post("/{conversation_id}/resolve", response_model=ConversationResponse)
async def resolve_conversation(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversation = await service.set_status(
            db,
            owner_id=current_user.id,
            conversation_id=conversation_id,
            status="resolved",
            needs_human=False,
        )
        return _serialize_conversation(conversation)
    except Exception as exc:
        raise _map_conversation_error(exc) from exc


@router.post("/{conversation_id}/block", response_model=ConversationResponse)
@router.post("/{conversation_id}/block-customer", response_model=ConversationResponse)
async def block_customer(
    conversation_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        conversation = await service.block_customer(db, owner_id=current_user.id, conversation_id=conversation_id)
        return _serialize_conversation(conversation)
    except Exception as exc:
        raise _map_conversation_error(exc) from exc
