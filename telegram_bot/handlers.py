"""
Telegram Bot Handlers.
Command and message handlers for the bot using pyTelegramBotAPI.
"""
import httpx
from telegram_bot.config import bot_settings
import logging
import json
import os

logger = logging.getLogger(__name__)

# Bot instance (will be set from bot.py)
bot = None

def set_bot(bot_instance):
    global bot
    bot = bot_instance

def start_command(message):
    """Handle /start command."""
    bot.reply_to(
        message,
        "مرحباً بك في RAGMind Bot! 🤖\n\n"
        "أنا هنا للإجابة على أسئلتك بناءً على مشروع التخرج.\n"
        "فقط أرسل سؤالك وسأجيب فوراً."
    )

def help_command(message):
    """Handle /help command."""
    bot.reply_to(
        message,
        "📚 دليل الاستخدام\n\n"
        "فقط أرسل سؤالك وسأقوم بالبحث في المستندات والإجابة عليك."
    )

def handle_message(message):
    """Handle text messages (queries)."""
    if message.text.startswith('/'):
        return
    
    # تثبيت المشروع على رقم 3 للمناقشة لضمان العمل
    project_id = 3 
    
    query = message.text
    thinking_msg = bot.reply_to(message, "🤔 جاري البحث في مستندات أحمد...")
    
    # التوكن اللي إحنا طلعناه من الـ Swagger
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGVzIjpbImFkbWluIiwidXNlciJdLCJpYXQiOjE3NzY1NDI0MTcsImV4cCI6MTc3NjU0NjAxN30.nncq-RjMaAZ-FIdwh6ivLKlSsj6dgBHwJnhVhw1FjCA"

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{bot_settings.api_base_url}/projects/{project_id}/query",
                json={
                    "query": query,
                    "top_k": 5,
                    "language": "ar"
                },
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        answer = f"💡 الإجابة:\n\n{result['answer']}\n\n"
        
        if result.get('sources'):
            answer += "📚 المصادر:\n"
            for i, source in enumerate(result['sources'][:3], 1):
                answer += f"{i}. {source['document_name']} ({source['similarity']:.1%})\n"
        
        bot.edit_message_text(
            answer,
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
        
    except Exception as e:
        logger.error(f"Error querying: {str(e)}")
        bot.edit_message_text(
            f"❌ حدث خطأ: تأكد من تشغيل الباكند ورفع الملفات في مشروع رقم {project_id}",
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )