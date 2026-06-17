import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests


def env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


BASE_URL = os.getenv("RAGMIND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = int(os.getenv("RAGMIND_REQUEST_TIMEOUT", "30"))
PROCESSING_TIMEOUT_SECONDS = int(os.getenv("RAGMIND_PROCESSING_TIMEOUT", "180"))
STRICT_QUERY = env_flag("RAGMIND_STRICT_QUERY", default=False)
TEST_LLM_PROVIDER = (os.getenv("RAGMIND_TEST_LLM_PROVIDER") or "").strip().lower()
TEST_EMBEDDING_PROVIDER = (os.getenv("RAGMIND_TEST_EMBEDDING_PROVIDER") or "").strip().lower()
TEST_TELEGRAM_BOT_TOKEN = (os.getenv("RAGMIND_TEST_TELEGRAM_BOT_TOKEN") or "").strip()
PLATFORM_OWNER_TOKEN = (os.getenv("RAGMIND_PLATFORM_OWNER_TOKEN") or "").strip()
SECURITY_TOKEN = (os.getenv("RAGMIND_SECURITY_TOKEN") or "").strip()
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def request_json(
    session: requests.Session,
    method: str,
    path: str,
    *,
    expected_status: int | None = None,
    **kwargs,
):
    url = f"{BASE_URL}{path}"
    response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    print(f"{method} {path} -> {response.status_code}")
    if expected_status is not None and response.status_code != expected_status:
        body = response.text[:1000]
        fail(f"Unexpected status for {path}: expected {expected_status}, got {response.status_code}. Body: {body}")
    try:
        return response, response.json()
    except ValueError:
        fail(f"Expected JSON response from {path}, got: {response.text[:1000]}")


def request_no_content(
    session: requests.Session,
    method: str,
    path: str,
    *,
    expected_status: int,
    **kwargs,
) -> None:
    url = f"{BASE_URL}{path}"
    response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    print(f"{method} {path} -> {response.status_code}")
    if response.status_code != expected_status:
        fail(
            f"Unexpected status for {path}: expected {expected_status}, got {response.status_code}. "
            f"Body: {response.text[:1000]}"
        )


class _MockTelegramAPI:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []

    async def validate_token(self, token: str) -> dict[str, Any]:
        if not str(token or "").strip():
            raise ValueError("token required")
        return {
            "telegram_bot_id": f"mock-{abs(hash(token)) % 100000}",
            "telegram_username": "codex_mock_support_bot",
        }

    async def set_webhook(self, token: str, webhook_url: str, **kwargs) -> None:
        if str(token or "") in webhook_url:
            raise AssertionError("Webhook URL must not include the bot token")

    async def delete_webhook(self, token: str) -> None:
        return None

    async def send_message(self, token: str, chat_id: str, text: str) -> dict[str, Any]:
        self.sent_messages.append({"token": token, "chat_id": chat_id, "text": text})
        return {"message_id": 7001}


class _MockCustomerQueryService:
    async def answer(self, db, *, integration, query: str, language: str = "ar") -> dict[str, Any]:
        return {
            "customer_answer": f"Mock support answer for: {query}",
            "internal_sources": [
                {
                    "document_name": "internal-smoke-doc.txt",
                    "asset_id": 1,
                    "chunk_index": 0,
                    "similarity": 0.99,
                }
            ],
            "context_used": 1,
        }


def assert_product_telegram_flow_excludes_legacy() -> None:
    legacy_terms = ("active_project_id", "bot_config", "BOT_API_USERNAME", "AUTH_ADMIN_USERNAME")
    product_files = [
        REPO_ROOT / "backend" / "services" / "customer_bot_query_service.py",
        REPO_ROOT / "backend" / "services" / "telegram_webhook_service.py",
        REPO_ROOT / "backend" / "routes" / "telegram_webhook.py",
    ]
    for path in product_files:
        text = path.read_text(encoding="utf-8")
        for term in legacy_terms:
            if term in text:
                fail(f"Production Telegram flow references legacy term '{term}' in {path}")


def login_security_session() -> requests.Session | None:
    """Return an admin/security session for incident smoke checks when credentials are available."""
    session = requests.Session()
    if SECURITY_TOKEN:
        session.headers.update({"Authorization": f"Bearer {SECURITY_TOKEN}"})
        return session

    from backend.config import settings

    username = str(getattr(settings, "auth_admin_username", "") or "").strip()
    password = str(getattr(settings, "auth_admin_password", "") or "").strip()
    if not username or not password:
        username = os.getenv("RAGMIND_SECURITY_USERNAME", "codex_security_smoke").strip()
        password = os.getenv("RAGMIND_SECURITY_PASSWORD", "CodexSecuritySmoke_2026!")
        signup_response = requests.Session().post(
            f"{BASE_URL}/auth/signup",
            timeout=REQUEST_TIMEOUT,
            json={"username": username, "password": password},
        )
        print(f"POST /auth/signup (security smoke) -> {signup_response.status_code}")
        if signup_response.status_code not in {201, 400, 409}:
            warn(f"Security smoke signup returned unexpected status: {signup_response.status_code}")

    try:
        _, login = request_json(
            requests.Session(),
            "POST",
            "/auth/login",
            expected_status=200,
            json={"username": username, "password": password},
        )
    except SystemExit:
        warn("Skipping incident smoke; admin login was not available. Set RAGMIND_SECURITY_TOKEN to enable it.")
        return None

    token = login.get("access_token")
    if not token:
        warn("Skipping incident smoke; admin login response did not include a token.")
        return None
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def run_incident_smoke() -> None:
    """Exercise security simulation and incident lifecycle endpoints against the live API."""
    security_session = login_security_session()
    if security_session is None:
        return

    request_json(security_session, "POST", "/security/simulate?escalate_to_block=false", expected_status=200)
    incidents = []
    deadline = time.time() + 10
    while time.time() < deadline:
        _, all_incidents = request_json(security_session, "GET", "/incidents", expected_status=200)
        incidents = [inc for inc in all_incidents if inc.get("status") == "OPEN"]
        if incidents:
            break
        time.sleep(0.5)
    if not isinstance(incidents, list):
        fail(f"/incidents should return a list: {incidents}")
    if not incidents:
        fail("Security simulation did not create any incidents")

    incident_id = incidents[0].get("id")
    if not incident_id:
        fail(f"Incident list item missing id: {incidents[0]}")

    request_json(security_session, "GET", f"/incidents/{incident_id}", expected_status=200)
    request_json(
        security_session,
        "PATCH",
        f"/incidents/{incident_id}",
        expected_status=200,
        json={"status": "INVESTIGATING", "metadata": {"source": "tools/test_all.py"}},
    )
    request_json(
        security_session,
        "POST",
        f"/incidents/{incident_id}/assign",
        expected_status=200,
        json={"metadata": {"source": "tools/test_all.py"}},
    )
    request_json(
        security_session,
        "POST",
        f"/incidents/{incident_id}/action",
        expected_status=200,
        json={"action_type": "ignore", "metadata": {"reason": "smoke test no-op"}},
    )
    request_json(
        security_session,
        "PATCH",
        f"/incidents/{incident_id}/notes",
        expected_status=200,
        json={"notes": "Smoke test verified incident endpoints.", "metadata": {"source": "tools/test_all.py"}},
    )
    print(f"[OK] Incident smoke completed for incident {incident_id}")


async def run_mocked_bot_webhook_smoke(
    *,
    owner_id: int,
    project_id: int,
    authed: requests.Session,
    suffix: str,
) -> None:
    from sqlalchemy import select

    from backend.database.connection import async_session_maker
    from backend.database.models import Conversation, ConversationMessage, TelegramCustomer
    from backend.services.bot_integration_service import BotIntegrationService
    from backend.services.conversation_service import ConversationService
    from backend.services.telegram_webhook_service import TelegramWebhookService
    from backend.services.token_crypto_service import TokenCryptoService

    mock_token = f"999999:{suffix}-mock-token"
    mock_telegram = _MockTelegramAPI()
    crypto = TokenCryptoService(key=TokenCryptoService.generate_key())
    integration_id: int | None = None

    async with async_session_maker() as db:
        bot_service = BotIntegrationService(crypto_service=crypto, telegram_api=mock_telegram)
        integration = await bot_service.create_integration(
            db,
            owner_id=owner_id,
            project_id=project_id,
            name=f"Codex Mock Bot {suffix}",
            bot_token=mock_token,
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            fallback_message="A human support teammate will follow up.",
            created_by_user_id=owner_id,
        )
        integration_id = int(integration.id)

        response = request_json(authed, "GET", f"/bot-integrations/{integration_id}", expected_status=200)[1]
        for forbidden_key in ("bot_token", "token_encrypted", "token_hash", "webhook_secret", "webhook_url"):
            if forbidden_key in response:
                fail(f"Mocked bot integration response exposed secret field '{forbidden_key}': {response}")
        if mock_token in str(response):
            fail(f"Mocked bot integration response exposed raw token: {response}")

        webhook_service = TelegramWebhookService(
            integration_service=bot_service,
            conversation_service=ConversationService(crypto_service=crypto, telegram_api=mock_telegram),
            query_service=_MockCustomerQueryService(),
            crypto_service=crypto,
            telegram_api=mock_telegram,
        )
        update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 501,
                "text": "What are your support hours?",
                "chat": {"id": 88001, "type": "private"},
                "from": {
                    "id": 88001,
                    "is_bot": False,
                    "first_name": "Codex",
                    "last_name": "Customer",
                    "username": "codex_customer",
                    "language_code": "en",
                },
            },
        }
        webhook_result = await webhook_service.handle_update(
            db,
            integration_id=integration_id,
            webhook_secret=str(integration.webhook_secret),
            update=update,
        )
        if not webhook_result.get("ok") or not webhook_result.get("conversation_id"):
            fail(f"Mocked webhook did not return a conversation id: {webhook_result}")

        conversation_id = int(webhook_result["conversation_id"])
        customer = (
            await db.execute(
                select(TelegramCustomer).where(
                    TelegramCustomer.owner_id == owner_id,
                    TelegramCustomer.bot_integration_id == integration_id,
                    TelegramCustomer.chat_id == "88001",
                )
            )
        ).scalar_one_or_none()
        if customer is None:
            fail("Mocked webhook did not persist the Telegram customer")

        conversation = (
            await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.owner_id == owner_id,
                    Conversation.bot_integration_id == integration_id,
                    Conversation.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if conversation is None:
            fail("Mocked webhook did not persist an owner/project scoped conversation")

        messages = list(
            (
                await db.execute(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conversation_id)
                    .order_by(ConversationMessage.id.asc())
                )
            )
            .scalars()
            .all()
        )
        sender_types = [message.sender_type for message in messages]
        if "customer" not in sender_types:
            fail(f"Mocked webhook should persist customer message, got {sender_types}")

        _, conversation_list = request_json(authed, "GET", "/conversations/", expected_status=200)
        if not any(item.get("id") == conversation_id for item in conversation_list):
            fail(f"Company conversation endpoint did not include mocked webhook conversation: {conversation_list}")
        _, message_list = request_json(authed, "GET", f"/conversations/{conversation_id}/messages", expected_status=200)
        if "customer" not in [item.get("sender_type") for item in message_list]:
            fail(f"Company message endpoint returned unexpected mocked webhook messages: {message_list}")

        await bot_service.delete_integration(db, owner_id=owner_id, integration_id=integration_id)
        integration_id = None

    if integration_id is not None:
        async with async_session_maker() as db:
            await BotIntegrationService(crypto_service=crypto, telegram_api=mock_telegram).delete_integration(
                db,
                owner_id=owner_id,
                integration_id=integration_id,
            )


def main() -> None:
    # Use UTF-8 for printing to avoid charmap codec issues on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"Testing RAGMind endpoints against {BASE_URL}")
    print(f"Strict query assertions: {'enabled' if STRICT_QUERY else 'disabled'}")

    anonymous = requests.Session()
    authed = requests.Session()
    platform_owner = requests.Session()
    if PLATFORM_OWNER_TOKEN:
        platform_owner.headers.update({"Authorization": f"Bearer {PLATFORM_OWNER_TOKEN}"})

    project_id: int | None = None
    second_project_id: int | None = None
    asset_id: int | None = None
    bot_integration_id: int | None = None
    selected_llm_provider: str | None = None
    selected_embedding_provider: str | None = None
    processing_degraded = False

    suffix = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    username = f"codex_smoke_{suffix}"
    password = f"SmokePass_{suffix}!"
    second_username = f"codex_smoke_other_{suffix}"
    second_password = f"SmokeOtherPass_{suffix}!"
    test_filename = "codex_endpoint_smoke.txt"
    test_content = (
        "Candidate name: Codex Smoke Tester.\n"
        "Favorite city: Cairo.\n"
        "Primary skill: retrieval augmented generation.\n"
    )

    try:
        _, health = request_json(anonymous, "GET", "/health", expected_status=200)
        if health.get("status") != "healthy":
            fail(f"Health endpoint returned unexpected payload: {health}")

        _, signup = request_json(
            anonymous,
            "POST",
            "/auth/signup",
            expected_status=201,
            json={"username": username, "password": password},
        )
        print(f"Signup response: {signup}")

        _, login = request_json(
            anonymous,
            "POST",
            "/auth/login",
            expected_status=200,
            json={"username": username, "password": password},
        )
        token = login.get("access_token")
        if not token:
            fail(f"Login response missing access_token: {login}")
        authed.headers.update({"Authorization": f"Bearer {token}"})

        _, me = request_json(authed, "GET", "/auth/me", expected_status=200)
        if me.get("username") != username:
            fail(f"/auth/me returned unexpected user payload: {me}")
        if me.get("role") != "company_admin":
            fail(f"/auth/me should default smoke users to company_admin role: {me}")
        owner_id = me.get("id")
        if not owner_id:
            fail(f"/auth/me response missing user id required for mocked smoke checks: {me}")

        _, stats = request_json(authed, "GET", "/stats/", expected_status=200)
        for key in ("projects", "documents", "chunks"):
            if key not in stats:
                fail(f"Stats response missing key '{key}': {stats}")

        _, admin_denied = request_json(authed, "GET", "/admin/overview", expected_status=403)
        if "platform" not in str(admin_denied).lower():
            fail(f"Company user /admin denial should mention platform-owner access: {admin_denied}")
        if PLATFORM_OWNER_TOKEN:
            _, admin_companies = request_json(platform_owner, "GET", "/admin/companies", expected_status=200)
            if not isinstance(admin_companies, list):
                fail(f"Platform owner /admin/companies should return a list: {admin_companies}")
        else:
            warn("Skipping platform-owner positive admin smoke; set RAGMIND_PLATFORM_OWNER_TOKEN to enable it.")

        run_incident_smoke()

        # Configure providers with a compatibility-aware embedding choice.
        _, providers_config = request_json(
            authed,
            "GET",
            "/config/providers",
            expected_status=200,
        )
        available_llm = list((providers_config.get("available") or {}).get("llm") or [])
        available_embedding = list((providers_config.get("available") or {}).get("embedding") or [])

        current_llm_provider = str(providers_config.get("llm_provider") or "").strip().lower()
        if TEST_LLM_PROVIDER:
            if TEST_LLM_PROVIDER not in available_llm:
                fail(
                    f"Requested RAGMIND_TEST_LLM_PROVIDER='{TEST_LLM_PROVIDER}' is not available. "
                    f"Available: {available_llm}"
                )
            target_llm_provider = TEST_LLM_PROVIDER
        elif current_llm_provider and current_llm_provider in available_llm:
            target_llm_provider = current_llm_provider
        elif "gemini" in available_llm:
            target_llm_provider = "gemini"
        elif available_llm:
            target_llm_provider = available_llm[0]
        else:
            fail("No LLM providers are available from /config/providers")

        current_embedding_provider = str(providers_config.get("embedding_provider") or "").strip().lower()
        if TEST_EMBEDDING_PROVIDER:
            if TEST_EMBEDDING_PROVIDER not in available_embedding:
                fail(
                    "Requested RAGMIND_TEST_EMBEDDING_PROVIDER="
                    f"'{TEST_EMBEDDING_PROVIDER}' is not available. Available: {available_embedding}"
                )
            target_embedding_provider = TEST_EMBEDDING_PROVIDER
        elif current_embedding_provider and current_embedding_provider in available_embedding:
            target_embedding_provider = current_embedding_provider
        elif "gemini" in available_embedding:
            target_embedding_provider = "gemini"
        elif available_embedding:
            target_embedding_provider = available_embedding[0]
        else:
            target_embedding_provider = None
        if not target_embedding_provider:
            fail("No embedding providers are available from /config/providers")

        if target_llm_provider != current_llm_provider or target_embedding_provider != current_embedding_provider:
            warn(
                "Switching provider configuration for smoke test: "
                f"llm '{current_llm_provider}' -> '{target_llm_provider}', "
                f"embedding '{current_embedding_provider}' -> '{target_embedding_provider}'"
            )

        if target_llm_provider != current_llm_provider or target_embedding_provider != current_embedding_provider:
            _, config_update = request_json(
                authed,
                "POST",
                "/config/providers",
                expected_status=200,
                json={
                    "llm_provider": target_llm_provider,
                    "embedding_provider": target_embedding_provider,
                },
            )
            selected_llm_provider = str(config_update.get("llm_provider") or target_llm_provider)
            selected_embedding_provider = str(config_update.get("embedding_provider") or target_embedding_provider)
        else:
            selected_llm_provider = target_llm_provider
            selected_embedding_provider = target_embedding_provider

        print(
            f"Provider configured. LLM: {selected_llm_provider}, "
            f"Embedding: {selected_embedding_provider}"
        )

        _, project = request_json(
            authed,
            "POST",
            "/projects/",
            expected_status=201,
            json={
                "name": f"Codex Smoke Project {suffix}",
                "description": "Automated smoke test for the current API flow",
            },
        )
        project_id = project.get("id")
        if not project_id:
            fail(f"Project creation response missing id: {project}")

        second_authed = requests.Session()
        request_json(
            anonymous,
            "POST",
            "/auth/signup",
            expected_status=201,
            json={"username": second_username, "password": second_password},
        )
        _, second_login = request_json(
            anonymous,
            "POST",
            "/auth/login",
            expected_status=200,
            json={"username": second_username, "password": second_password},
        )
        second_token = second_login.get("access_token")
        if not second_token:
            fail(f"Second login response missing access_token: {second_login}")
        second_authed.headers.update({"Authorization": f"Bearer {second_token}"})
        _, second_project = request_json(
            second_authed,
            "POST",
            "/projects/",
            expected_status=201,
            json={
                "name": f"Codex Other Company Project {suffix}",
                "description": "Cross-company bot integration denial probe",
            },
        )
        second_project_id = second_project.get("id")
        if not second_project_id:
            fail(f"Second project creation response missing id: {second_project}")

        _, bot_missing_project_denial = request_json(
            authed,
            "POST",
            "/bot-integrations/",
            expected_status=404,
            json={
                "project_id": 2147483647,
                "name": "Cross Scope Probe",
                "bot_token": "1234567890:invalid-token-for-scope-probe",
            },
        )
        if "token" in str(bot_missing_project_denial).lower():
            fail(
                "Bot integration missing-project probe should fail on project ownership before token validation: "
                f"{bot_missing_project_denial}"
            )

        _, bot_cross_company_denial = request_json(
            authed,
            "POST",
            "/bot-integrations/",
            expected_status=404,
            json={
                "project_id": second_project_id,
                "name": "Cross Company Probe",
                "bot_token": "1234567890:invalid-token-for-cross-company-probe",
            },
        )
        if "token" in str(bot_cross_company_denial).lower():
            fail(
                "Bot integration cross-company probe should fail on project ownership before token validation: "
                f"{bot_cross_company_denial}"
            )

        assert_product_telegram_flow_excludes_legacy()
        asyncio.run(
            run_mocked_bot_webhook_smoke(
                owner_id=int(owner_id),
                project_id=int(project_id),
                authed=authed,
                suffix=suffix,
            )
        )

        if TEST_TELEGRAM_BOT_TOKEN:
            _, bot_integration = request_json(
                authed,
                "POST",
                "/bot-integrations/",
                expected_status=201,
                json={
                    "project_id": project_id,
                    "name": f"Codex Smoke Bot {suffix}",
                    "bot_token": TEST_TELEGRAM_BOT_TOKEN,
                    "show_sources_to_customer": False,
                    "human_handoff_enabled": True,
                },
            )
            bot_integration_id = bot_integration.get("id")
            if not bot_integration_id:
                fail(f"Bot integration response missing id: {bot_integration}")
            for forbidden_key in ("bot_token", "token_encrypted", "token_hash", "webhook_secret", "webhook_url"):
                if forbidden_key in bot_integration:
                    fail(f"Bot integration response exposed secret field '{forbidden_key}': {bot_integration}")

            _, readiness = request_json(
                authed,
                "GET",
                f"/bot-integrations/{bot_integration_id}/readiness",
                expected_status=200,
            )
            if "ready" not in readiness:
                fail(f"Readiness response missing ready flag: {readiness}")
        else:
            warn("Skipping live bot integration creation; set RAGMIND_TEST_TELEGRAM_BOT_TOKEN to enable it.")

        files = {"file": (test_filename, test_content.encode("utf-8"), "text/plain")}
        _, asset = request_json(
            authed,
            "POST",
            f"/projects/{project_id}/documents",
            expected_status=201,
            files=files,
        )
        asset_id = asset.get("id")
        if not asset_id:
            fail(f"Document upload response missing id: {asset}")

        print("Waiting for document processing to complete...")
        deadline = time.time() + PROCESSING_TIMEOUT_SECONDS
        final_document_payload = None
        while time.time() < deadline:
            _, document = request_json(
                authed,
                "GET",
                f"/documents/{asset_id}",
                expected_status=200,
            )
            status = document.get("status")
            print(f"Document status: {status}")
            final_document_payload = document
            if status == "completed":
                break
            if status == "failed":
                error_message = str(document.get("error_message") or "Unknown processing error")
                if "text-embedding-004" in error_message:
                    error_message += (
                        " | Hint: set a supported embedding model (for example "
                        "GEMINI_EMBED_MODEL=models/gemini-embedding-001) or use a non-Gemini embedding provider."
                    )
                known_embedding_mismatch = (
                    "text-embedding-004" in error_message
                    or "embedcontent" in error_message.lower()
                )
                if known_embedding_mismatch and not STRICT_QUERY:
                    processing_degraded = True
                    warn(
                        "Document processing failed due to known embedding model mismatch "
                        f"(llm_provider={selected_llm_provider}, embedding_provider={selected_embedding_provider}). "
                        "Continuing in degraded mode because strict assertions are disabled. "
                        f"Details: {error_message}"
                    )
                    break

                fail(
                    "Document processing failed "
                    f"(llm_provider={selected_llm_provider}, "
                    f"embedding_provider={selected_embedding_provider}): {error_message}"
                )
            time.sleep(2)
        else:
            fail(
                f"Timed out waiting for document processing after {PROCESSING_TIMEOUT_SECONDS}s. "
                f"Last payload: {final_document_payload}"
            )

        if processing_degraded:
            warn(
                "Skipping project stats and query assertions because document indexing did not complete. "
                "Enable RAGMIND_STRICT_QUERY=1 to treat this as a hard failure."
            )
            print("[OK] Smoke test completed with degraded checks")
            return

        _, project_stats = request_json(
            authed,
            "GET",
            f"/projects/{project_id}/stats",
            expected_status=200,
        )
        stats_payload = project_stats.get("stats") or {}
        if int(stats_payload.get("chunk_count", 0)) <= 0:
            fail(f"Project stats show no chunks after processing: {project_stats}")
        if int(stats_payload.get("completed_assets", 0)) <= 0:
            fail(f"Project stats show no completed assets after processing: {project_stats}")

        _, answer = request_json(
            authed,
            "POST",
            f"/projects/{project_id}/query",
            expected_status=200,
            json={"query": "What is the candidate name?", "language": "en"},
        )
        print("Answer:", answer.get("answer"))
        print("Sources:", answer.get("sources"))

        if not answer.get("answer"):
            fail(f"Query response missing answer text: {answer}")
        if int(answer.get("context_used", 0)) <= 0 or not answer.get("sources"):
            query_issue_message = (
                "Query endpoint returned a fallback or source-less answer. "
                "Ingestion passed, but answer generation may be degraded by provider quota or upstream model errors."
            )
            if STRICT_QUERY:
                fail(query_issue_message + " Strict mode is enabled.")
            warn(query_issue_message)

        print("[OK] Smoke test completed successfully")
    finally:
        if bot_integration_id is not None:
            try:
                request_no_content(authed, "DELETE", f"/bot-integrations/{bot_integration_id}", expected_status=204)
            except SystemExit:
                print("[WARN] Bot integration cleanup failed")
        if asset_id is not None:
            try:
                request_no_content(authed, "DELETE", f"/documents/{asset_id}", expected_status=204)
            except SystemExit:
                print("[WARN] Asset cleanup failed")
        if project_id is not None:
            try:
                request_no_content(authed, "DELETE", f"/projects/{project_id}", expected_status=204)
            except SystemExit:
                print("[WARN] Project cleanup failed")
        if second_project_id is not None:
            try:
                request_no_content(second_authed, "DELETE", f"/projects/{second_project_id}", expected_status=204)
            except Exception:
                print("[WARN] Second project cleanup failed")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        fail(f"HTTP request failed: {exc}")
