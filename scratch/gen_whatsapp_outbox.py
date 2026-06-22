import sys

def create_whatsapp_outbox(source, target):
    with open(source, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace("telegram_outbox", "whatsapp_outbox")
    content = content.replace("TelegramCustomer", "WhatsAppCustomer")
    content = content.replace("BotIntegration", "WhatsAppIntegration")
    content = content.replace("telegram_api", "whatsapp_api")
    content = content.replace("telegram_message_id", "whatsapp_message_id")
    content = content.replace("telegram_customer_id", "whatsapp_customer_id")
    content = content.replace("bot_integration_id", "whatsapp_integration_id")
    content = content.replace("telegram_outbox_max_delivery_attempts", "whatsapp_outbox_max_delivery_attempts")
    content = content.replace("telegram_outbox_claim_timeout_seconds", "whatsapp_outbox_claim_timeout_seconds")
    content = content.replace("telegram_outbox_retry_base_seconds", "whatsapp_outbox_retry_base_seconds")
    content = content.replace("telegram_outbox_retry_max_seconds", "whatsapp_outbox_retry_max_seconds")

    # The telegram api handles sending. WhatsApp needs a custom send request.
    # So I will replace the telegram api imports and logic with an HTTP call to the bridge.

    content = content.replace(
        "from backend.services.telegram_api_service import TelegramAPIError, TelegramAPIService",
        "import httpx"
    )
    content = content.replace("from backend.services.token_crypto_service import TokenCryptoService", "")
    content = content.replace("    crypto_service = TokenCryptoService()", "")
    content = content.replace("    telegram_api = TelegramAPIService()", "    import httpx")
    
    # replace sending logic
    send_logic_orig = """                try:
                    token = crypto_service.decrypt_token(integration.token_encrypted)
                except Exception:
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    message.delivery_next_attempt_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                # Claim before external call to reduce duplicate sends across workers.
                message.delivery_status = "sending"
                message.delivery_claimed_at = datetime.now(timezone.utc)
                message.delivery_next_attempt_at = None
                message.delivery_attempts = int(message.delivery_attempts or 0) + 1
                claimed_count += 1
                if was_stale_claim:
                    recovered_count += 1
                await db.commit()

                try:
                    result_payload = await whatsapp_api.send_message(token, customer.chat_id, message_text)
                except TelegramAPIError as exc:"""

    send_logic_new = """                # Claim before external call to reduce duplicate sends across workers.
                message.delivery_status = "sending"
                message.delivery_claimed_at = datetime.now(timezone.utc)
                message.delivery_next_attempt_at = None
                message.delivery_attempts = int(message.delivery_attempts or 0) + 1
                claimed_count += 1
                if was_stale_claim:
                    recovered_count += 1
                await db.commit()

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://whatsapp-bridge:3002/api/sessions/{integration.id}/send",
                            json={"jid": customer.phone_number, "text": message_text},
                            timeout=10.0
                        )
                        response.raise_for_status()
                        result_payload = response.json()
                except httpx.HTTPError as exc:"""

    content = content.replace(send_logic_orig, send_logic_new)
    
    content = content.replace("customer.chat_id", "customer.phone_number")
    content = content.replace("logger.warning(\"Telegram outbox delivery failed", "logger.warning(\"WhatsApp outbox delivery failed")
    content = content.replace("logger.exception(\"Unexpected telegram outbox error", "logger.exception(\"Unexpected WhatsApp outbox error")
    
    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)

create_whatsapp_outbox("backend/tasks/telegram_outbox.py", "backend/tasks/whatsapp_outbox.py")
