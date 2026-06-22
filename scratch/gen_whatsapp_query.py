import sys

def create_whatsapp_query(source, target):
    with open(source, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace("telegram", "whatsapp")
    content = content.replace("Telegram", "WhatsApp")
    content = content.replace("TELEGRAM", "WHATSAPP")
    content = content.replace("BotIntegration", "WhatsAppIntegration")
    content = content.replace("generate_bot_reply", "generate_whatsapp_reply")
    content = content.replace("Bot", "WhatsApp")
    content = content.replace("bot_integration", "whatsapp_integration")
    content = content.replace("telegram_username", "phone_number")
    
    # Also fix some specifics if needed
    # customer is WhatsAppCustomer now, there is no language_code for whatsapp_customer usually
    content = content.replace("""    language_code = str(getattr(customer, "language_code", "") or "").lower()""", 
                              """    # WhatsApp might not provide language, default to en or use settings\n    language_code = "en\"""")

    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)

create_whatsapp_query("backend/tasks/telegram_query.py", "backend/tasks/whatsapp_query.py")
