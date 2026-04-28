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

CONFIG_FILE = "bot_config.json"

def set_bot(bot_instance):
    global bot
    bot = bot_instance

def get_active_project():
    """Get active project ID from config."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("active_project_id")
        except:
            return None
    return None

def start_command(message):
    """Handle /start command."""
    bot.reply_to(
        message,
        "مرحباً بك في RAGMind Bot! 🤖\n\n"
        "أنا هنا للإجابة على أسئلتك بناءً على المشروع النشط.\n"
        "فقط أرسل سؤالك وسأجيب فوراً."
    )

def help_command(message):
    """Handle /help command."""
    bot.reply_to(
        message,
        "📚 دليل الاستخدام\n\n"
        "فقط أرسل سؤالك كتابةً وسأقوم بالبحث في مستندات المشروع النشط والإجابة عليك.\n"
        "لا توجد أوامر معقدة!"
    )

def handle_message(message):
    """Handle text messages (queries)."""
    # Ignore commands
    if message.text.startswith('/'):
        return
    
    project_id = get_active_project()
    
    if not project_id:
        bot.reply_to(
            message,
            "⚠️ عذراً، البوت غير مرتبط بمشروع حالياً.\n"
            "يرجى التواصل مع المسؤول لتحديد مشروع نشط."
        )
        return
    
    query = message.text
    
    # Send thinking message
    thinking_msg = bot.reply_to(message, "🤔 جاري البحث عن الإجابة...")
    
    try:
        # Query API
        with httpx.Client() as client:
            response = client.post(
                f"{bot_settings.api_base_url}/projects/{project_id}/query",
                json={
                    "query": query,
                    "top_k": 5,
                    "language": "ar"
                },
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        # Format answer
        answer = f"💡 الإجابة:\n\n{result['answer']}\n\n"
        
        if result.get('sources'):
            answer += "📚 المصادر:\n"
            for i, source in enumerate(result['sources'][:3], 1):
                answer += f"{i}. {source['document_name']} "
                answer += f"({source['similarity']:.1%})\n"
        
        bot.edit_message_text(
            answer,
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
        
    except Exception as e:
        logger.error(f"Error querying: {str(e)}")
        bot.edit_message_text(
            f"❌ حدث خطأ في معالجة السؤال: {str(e)}",
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
