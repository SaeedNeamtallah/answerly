with open('backend/services/customer_bot_query_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '            language=language,\n        )',
    '            language=language,\n            custom_system_prompt=integration.system_prompt,\n        )'
)

with open('backend/services/customer_bot_query_service.py', 'w', encoding='utf-8') as f:
    f.write(text)
