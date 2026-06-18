with open('backend/routes/bot_integrations.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '    fallback_message: Optional[str] = Field(None, max_length=1000)\n\n\nclass BotIntegrationUpdate(BaseModel):',
    '    fallback_message: Optional[str] = Field(None, max_length=1000)\n    system_prompt: Optional[str] = Field(None, max_length=4000)\n\n\nclass BotIntegrationUpdate(BaseModel):'
)

text = text.replace(
    '    fallback_message: Optional[str] = Field(None, max_length=1000)\n\n\nclass BotTokenRotateRequest(BaseModel):',
    '    fallback_message: Optional[str] = Field(None, max_length=1000)\n    system_prompt: Optional[str] = Field(None, max_length=4000)\n\n\nclass BotTokenRotateRequest(BaseModel):'
)

text = text.replace(
    '    fallback_message: Optional[str]\n    last_error: Optional[str]',
    '    fallback_message: Optional[str]\n    system_prompt: Optional[str]\n    last_error: Optional[str]'
)

text = text.replace(
    '        fallback_message=integration.fallback_message,\n        last_error=integration.last_error,',
    '        fallback_message=integration.fallback_message,\n        system_prompt=integration.system_prompt,\n        last_error=integration.last_error,'
)

text = text.replace(
    '            fallback_message=payload.fallback_message,\n            created_by_user_id=current_user.id,',
    '            fallback_message=payload.fallback_message,\n            system_prompt=payload.system_prompt,\n            created_by_user_id=current_user.id,'
)

text = text.replace(
    '            fallback_message=payload.fallback_message,\n            fallback_message_provided="fallback_message" in payload.model_fields_set,',
    '            fallback_message=payload.fallback_message,\n            system_prompt=payload.system_prompt,\n            fallback_message_provided="fallback_message" in payload.model_fields_set,\n            system_prompt_provided="system_prompt" in payload.model_fields_set,'
)

with open('backend/routes/bot_integrations.py', 'w', encoding='utf-8') as f:
    f.write(text)
