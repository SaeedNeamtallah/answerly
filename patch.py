with open('backend/services/bot_integration_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '        fallback_message: str | None = None,\n        created_by_user_id: int | None = None,',
    '        fallback_message: str | None = None,\n        system_prompt: str | None = None,\n        created_by_user_id: int | None = None,'
)

text = text.replace(
    '            fallback_message=sanitize_optional_text(fallback_message, 1000),\n            created_by_user_id=created_by_user_id,',
    '            fallback_message=sanitize_optional_text(fallback_message, 1000),\n            system_prompt=sanitize_optional_text(system_prompt, 4000),\n            created_by_user_id=created_by_user_id,'
)

text = text.replace(
    '        fallback_message: str | None = None,\n        fallback_message_provided: bool = False,',
    '        fallback_message: str | None = None,\n        system_prompt: str | None = None,\n        fallback_message_provided: bool = False,\n        system_prompt_provided: bool = False,'
)

text = text.replace(
    '        if fallback_message_provided:\n            integration.fallback_message = sanitize_optional_text(fallback_message, 1000)\n\n        integration.webhook_url',
    '        if fallback_message_provided:\n            integration.fallback_message = sanitize_optional_text(fallback_message, 1000)\n        if system_prompt_provided:\n            integration.system_prompt = sanitize_optional_text(system_prompt, 4000)\n\n        integration.webhook_url'
)

with open('backend/services/bot_integration_service.py', 'w', encoding='utf-8') as f:
    f.write(text)
