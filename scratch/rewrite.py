import sys

def modify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Inject imports
    if 'WhatsAppIntegration' not in content:
        content = content.replace(
            'from backend.database.models import (\n    BotIntegration,\n    Conversation,\n    ConversationMessage,\n    TelegramCustomer,\n)',
            'from backend.database.models import (\n    BotIntegration,\n    Conversation,\n    ConversationMessage,\n    TelegramCustomer,\n    WhatsAppIntegration,\n    WhatsAppCustomer,\n)'
        )

    # Add get_or_create_whatsapp_customer before get_or_create_conversation
    if 'get_or_create_whatsapp_customer' not in content:
        whatsapp_customer_method = """
    async def get_or_create_whatsapp_customer(
        self,
        db: AsyncSession,
        *,
        integration: WhatsAppIntegration,
        phone_number: str,
        name: str | None = None,
    ) -> WhatsAppCustomer:
        stmt = select(WhatsAppCustomer).where(
            WhatsAppCustomer.whatsapp_integration_id == integration.id,
            WhatsAppCustomer.phone_number == phone_number,
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        if customer is None:
            customer = WhatsAppCustomer(
                owner_id=integration.owner_id,
                whatsapp_integration_id=integration.id,
                phone_number=phone_number,
            )

        customer.name = sanitize_text(name, max_length=120, strip_html=True, allow_newlines=False) or None
        customer.last_seen_at = self._now()
        db.add(customer)
        await db.flush()
        return customer

    async def get_or_create_conversation(
"""
        content = content.replace('    async def get_or_create_conversation(\n', whatsapp_customer_method[1:])

    # Add get_or_create_whatsapp_conversation before find_existing_customer_message
    if 'get_or_create_whatsapp_conversation' not in content:
        whatsapp_conv_method = """
    async def get_or_create_whatsapp_conversation(
        self,
        db: AsyncSession,
        *,
        integration: WhatsAppIntegration,
        customer: WhatsAppCustomer,
    ) -> Conversation:
        stmt = (
            select(Conversation)
            .where(
                Conversation.whatsapp_integration_id == integration.id,
                Conversation.whatsapp_customer_id == customer.id,
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
                whatsapp_integration_id=integration.id,
                whatsapp_customer_id=customer.id,
                project_id=integration.project_id,
                channel="whatsapp",
                status="open",
            )
            db.add(conversation)
            await db.flush()
        return conversation

    async def find_existing_customer_message(
"""
        content = content.replace('    async def find_existing_customer_message(\n', whatsapp_conv_method[1:])
        
    # Add find_existing_whatsapp_message before save_message
    if 'find_existing_whatsapp_message' not in content:
        wa_msg_method = """
    async def find_existing_whatsapp_message(
        self,
        db: AsyncSession,
        *,
        integration_id: int,
        customer_id: int,
        whatsapp_message_id: str,
    ) -> ConversationMessage | None:
        stmt = select(ConversationMessage).where(
            ConversationMessage.whatsapp_integration_id == int(integration_id),
            ConversationMessage.whatsapp_customer_id == int(customer_id),
            ConversationMessage.whatsapp_message_id == str(whatsapp_message_id),
        )
        result = await db.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def save_message(
"""
        content = content.replace('    async def save_message(\n', wa_msg_method[1:])

    # Add save_whatsapp_message before list_conversations
    if 'save_whatsapp_message' not in content:
        wa_save_msg_method = """
    async def save_whatsapp_message(
        self,
        db: AsyncSession,
        *,
        integration: WhatsAppIntegration,
        conversation: Conversation,
        sender_type: str,
        text: str,
        delivery_status: str = "none",
        customer: WhatsAppCustomer | None = None,
        agent_user_id: int | None = None,
        whatsapp_message_id: str | None = None,
        answer_sources: list[dict[str, Any]] | None = None,
        retrieval_metadata: dict[str, Any] | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> tuple[ConversationMessage, bool]:
        if sender_type not in MESSAGE_SENDER_TYPES:
            raise ConversationError("Unsupported message sender type")

        if sender_type == "customer" and whatsapp_message_id:
            existing = await self.find_existing_whatsapp_message(
                db,
                integration_id=integration.id,
                customer_id=int(customer.id) if customer else 0,
                whatsapp_message_id=whatsapp_message_id,
            )
            if existing is not None:
                return existing, False

        message = ConversationMessage(
            owner_id=integration.owner_id,
            whatsapp_integration_id=integration.id,
            conversation_id=conversation.id,
            whatsapp_customer_id=customer.id if customer else conversation.whatsapp_customer_id,
            sender_type=sender_type,
            agent_user_id=agent_user_id,
            text=self._clean_message_text(text),
            whatsapp_message_id=str(whatsapp_message_id) if whatsapp_message_id is not None else None,
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
            if sender_type == "customer" and whatsapp_message_id:
                existing = await self.find_existing_whatsapp_message(
                    db,
                    integration_id=integration.id,
                    customer_id=int(customer.id) if customer else 0,
                    whatsapp_message_id=whatsapp_message_id,
                )
                if existing is not None:
                    return existing, False
            raise
        return message, True

    async def list_conversations(
"""
        content = content.replace('    async def list_conversations(\n', wa_save_msg_method[1:])

    # Update list_conversations to selectinload whatsapp relations
    if 'selectinload(Conversation.whatsapp_customer)' not in content:
        content = content.replace(
            '            .options(selectinload(Conversation.customer), selectinload(Conversation.bot_integration))\n',
            '            .options(selectinload(Conversation.customer), selectinload(Conversation.bot_integration), selectinload(Conversation.whatsapp_customer), selectinload(Conversation.whatsapp_integration))\n'
        )

    # Update block_customer
    if 'customer = await db.get(WhatsAppCustomer, conversation.whatsapp_customer_id)' not in content:
        block_customer_orig = """        customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
        if customer is not None and customer.owner_id == int(owner_id):
            customer.is_blocked = True
            db.add(customer)"""
        block_customer_new = """        if conversation.channel == "whatsapp":
            customer = await db.get(WhatsAppCustomer, conversation.whatsapp_customer_id)
            if customer is not None and customer.owner_id == int(owner_id):
                customer.is_blocked = True
                db.add(customer)
        else:
            customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
            if customer is not None and customer.owner_id == int(owner_id):
                customer.is_blocked = True
                db.add(customer)"""
        content = content.replace(block_customer_orig, block_customer_new)

    # Update manual_reply
    if 'if conversation.channel == "whatsapp":' not in content:
        manual_reply_orig = """        integration = await db.get(BotIntegration, conversation.bot_integration_id)
        customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
        if integration is None or customer is None or integration.owner_id != int(owner_id):
            raise ConversationError("Conversation integration is unavailable")
        message, _ = await self.save_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="agent",
            agent_user_id=agent_user_id,
            text=text,
            delivery_status="pending",
        )"""
        manual_reply_new = """        if conversation.channel == "whatsapp":
            integration = await db.get(WhatsAppIntegration, conversation.whatsapp_integration_id)
            customer = await db.get(WhatsAppCustomer, conversation.whatsapp_customer_id)
            if integration is None or customer is None or integration.owner_id != int(owner_id):
                raise ConversationError("Conversation integration is unavailable")
            message, _ = await self.save_whatsapp_message(
                db,
                integration=integration,
                conversation=conversation,
                customer=customer,
                sender_type="agent",
                agent_user_id=agent_user_id,
                text=text,
                delivery_status="pending",
            )
        else:
            integration = await db.get(BotIntegration, conversation.bot_integration_id)
            customer = await db.get(TelegramCustomer, conversation.telegram_customer_id)
            if integration is None or customer is None or integration.owner_id != int(owner_id):
                raise ConversationError("Conversation integration is unavailable")
            message, _ = await self.save_message(
                db,
                integration=integration,
                conversation=conversation,
                customer=customer,
                sender_type="agent",
                agent_user_id=agent_user_id,
                text=text,
                delivery_status="pending",
            )"""
        content = content.replace(manual_reply_orig, manual_reply_new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

modify_file("backend/services/conversation_service.py")
