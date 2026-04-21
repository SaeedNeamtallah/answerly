"""
Telegram Bot Handlers.
Command and message handlers for the bot using pyTelegramBotAPI.
"""
import base64
import logging
import json
import os
import time
from typing import Optional

import httpx

from telegram_bot.config import BOT_CONFIG_PATH, bot_settings

logger = logging.getLogger(__name__)

# Bot instance (will be set from bot.py)
bot = None
_TOKEN_REFRESH_SKEW_SECONDS = 30
_token_cache = {
    "access_token": None,
    "exp": 0,
}

def set_bot(bot_instance):
    global bot
    bot = bot_instance


def _decode_jwt_exp(access_token: str) -> int:
    try:
        payload_part = access_token.split(".")[1]
        padding = "=" * (-len(payload_part) % 4)
        payload_raw = base64.urlsafe_b64decode(payload_part + padding)
        payload = json.loads(payload_raw.decode("utf-8"))
        return int(payload.get("exp") or 0)
    except Exception:
        return 0


def _is_cached_token_valid() -> bool:
    token = _token_cache.get("access_token")
    exp = int(_token_cache.get("exp") or 0)
    now = int(time.time())
    return bool(token) and exp > (now + _TOKEN_REFRESH_SKEW_SECONDS)


def _resolve_bot_credentials() -> tuple[str, str]:
    username = (
        os.getenv("BOT_API_USERNAME")
        or os.getenv("AUTH_ADMIN_USERNAME")
        or "admin"
    ).strip()
    password = (
        os.getenv("BOT_API_PASSWORD")
        or os.getenv("AUTH_ADMIN_PASSWORD")
        or ""
    ).strip()
    return username, password


def _obtain_access_token(client: httpx.Client, force_refresh: bool = False) -> str:
    if not force_refresh and _is_cached_token_valid():
        return str(_token_cache["access_token"])

    username, password = _resolve_bot_credentials()
    if not password:
        raise RuntimeError(
            "Bot API password is missing. Configure BOT_API_PASSWORD or AUTH_ADMIN_PASSWORD."
        )

    response = client.post(
        f"{bot_settings.api_base_url}/auth/login",
        json={
            "username": username,
            "password": password,
        },
        timeout=20.0,
    )
    response.raise_for_status()

    payload = response.json() if response.content else {}
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("auth/login returned an empty access_token")

    _token_cache["access_token"] = token
    _token_cache["exp"] = _decode_jwt_exp(token)
    return token


def _resolve_active_project_id() -> Optional[int]:
    try:
        if BOT_CONFIG_PATH.exists():
            with BOT_CONFIG_PATH.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            raw_id = config.get("active_project_id")
            if raw_id is not None:
                project_id = int(raw_id)
                if project_id > 0:
                    return project_id
    except Exception as exc:
        logger.warning("Failed to read bot config file: %s", exc)

    env_project_id = (os.getenv("BOT_ACTIVE_PROJECT_ID") or "").strip()
    if env_project_id:
        try:
            project_id = int(env_project_id)
            if project_id > 0:
                return project_id
        except ValueError:
            logger.warning("Invalid BOT_ACTIVE_PROJECT_ID value: %s", env_project_id)

    return None


def _save_active_project_id(project_id: int) -> None:
    try:
        config = {}
        if BOT_CONFIG_PATH.exists():
            with BOT_CONFIG_PATH.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
                if not isinstance(config, dict):
                    config = {}

        config["active_project_id"] = int(project_id)
        BOT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with BOT_CONFIG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("Failed to persist active project id to bot config: %s", exc)


def _query_backend_project(
    client: httpx.Client,
    *,
    project_id: int,
    query: str,
    token: str,
) -> httpx.Response:
    return client.post(
        f"{bot_settings.api_base_url}/projects/{project_id}/query",
        json={
            "query": query,
            "top_k": 5,
            "language": "ar"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )


def _fetch_first_accessible_project_id(client: httpx.Client, token: str) -> Optional[int]:
    try:
        response = client.get(
            f"{bot_settings.api_base_url}/projects/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20.0,
        )
        if response.status_code != 200:
            return None

        payload = response.json() if response.content else {}
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return None

        for item in items:
            if not isinstance(item, dict):
                continue
            raw_id = item.get("id")
            try:
                project_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if project_id > 0:
                return project_id
    except Exception as exc:
        logger.warning("Failed to fetch accessible projects for bot user: %s", exc)

    return None

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
    
    project_id = _resolve_active_project_id()
    if not project_id:
        bot.reply_to(
            message,
            "⚠️ لم يتم تحديد مشروع للبوت بعد. "
            "من لوحة التحكم افتح إعدادات البوت وحدد المشروع النشط أولاً."
        )
        return
    
    query = message.text
    thinking_msg = bot.reply_to(message, "🤔 جاري البحث في مستندات أحمد...")

    try:
        with httpx.Client(timeout=60.0) as client:
            token = _obtain_access_token(client)
            response = _query_backend_project(
                client,
                project_id=project_id,
                query=query,
                token=token,
            )

            # If token expired between cache check and query request, refresh once.
            if response.status_code == 401:
                token = _obtain_access_token(client, force_refresh=True)
                response = _query_backend_project(
                    client,
                    project_id=project_id,
                    query=query,
                    token=token,
                )

            # If configured project is stale/inaccessible, pick first accessible project and retry once.
            if response.status_code in (403, 404):
                fallback_project_id = _fetch_first_accessible_project_id(client, token)
                if fallback_project_id and fallback_project_id != project_id:
                    logger.info(
                        "Switching bot active project from %s to %s",
                        project_id,
                        fallback_project_id,
                    )
                    project_id = fallback_project_id
                    _save_active_project_id(project_id)
                    response = _query_backend_project(
                        client,
                        project_id=project_id,
                        query=query,
                        token=token,
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
        
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code if e.response is not None else 0
        logger.error("HTTP error querying project %s: %s", project_id, str(e))

        if status_code == 401:
            error_text = (
                "❌ فشل توثيق البوت مع الباكند. "
                "راجع BOT_API_USERNAME/BOT_API_PASSWORD أو AUTH_ADMIN_USERNAME/AUTH_ADMIN_PASSWORD في .env"
            )
        elif status_code == 403:
            error_text = (
                f"❌ لا توجد صلاحية للوصول إلى المشروع رقم {project_id}. "
                "اجعل المشروع النشط مملوكاً لنفس مستخدم البوت."
            )
        elif status_code == 404:
            error_text = f"❌ المشروع رقم {project_id} غير موجود. حدده من إعدادات البوت."
        else:
            error_text = f"❌ فشل الاستعلام من الباكند (HTTP {status_code})."

        bot.edit_message_text(
            error_text,
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
    except httpx.RequestError as e:
        logger.error("Network error querying backend: %s", str(e))
        bot.edit_message_text(
            "❌ تعذر الوصول إلى الباكند. تأكد أن خدمة backend تعمل وأن API_BASE_URL صحيح.",
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
    except Exception as e:
        logger.error(f"Error querying: {str(e)}")
        bot.edit_message_text(
            f"❌ حدث خطأ غير متوقع أثناء الاستعلام على المشروع رقم {project_id}",
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id
        )
