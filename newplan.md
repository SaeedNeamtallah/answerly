تمام. دي **الخطة النهائية المعدّلة** بكل اللي اتفقنا عليه، بدون حذف أي حاجة من الخطط القديمة، ومع إضافة دورك أنت كـ **Platform Owner / Super Admin**.

الفكرة الأساسية:
**ما نكسرش الـ RAG core الموجود.** الكود الحالي عنده flow واضح: upload documents → processing/chunking/embedding → vector search → answer generation، والـ query الحالي مربوط بـ `/projects/{project_id}/query` وبيحافظ على `owner_id` و `project_id` في الـ scoping. ده لازم يفضل زي ما هو. 

---

# الهدف النهائي للـ Agent

حوّل المشروع من:

```text
RAG app + single optional Telegram bot
```

إلى:

```text
B2B SaaS product:
- Platform Owner يشوف كل الشركات
- Company Admin يرفع ملفات ويعمل knowledge bases
- Company Admin يربط أكتر من Telegram bot
- كل bot مربوط بـ project/knowledge base
- Telegram customer يسأل البوت
- البوت يرد من ملفات الشركة فقط
- كل المحادثات تتخزن
- الشركة تشوف conversations بتاعة عملائها
- Platform Owner يشوف كل الشركات/projects/bots/conversations
```

---

# Roles المطلوبة

## 1. Platform Owner — أنت

ده مالك المنصة.

يقدر يشوف:

```text
كل الشركات المسجلة
كل projects
كل bot integrations
كل conversations
كل messages
كل errors
كل usage/stats
```

لكن من endpoints وصفحات admin مخصوصة، مش من نفس endpoints الشركة.

---

## 2. Company Admin — الشركة

كل user عادي في النظام حاليًا نعتبره:

```text
Company Account / Company Admin
```

الشركة تقدر:

```text
تعمل projects / knowledge bases
ترفع ملفات
تجرب الشات من الموقع
تربط Telegram bots
تشوف محادثات عملائها فقط
ترد manual reply لو محتاجة
تقفل conversation / escalate / block customer
```

---

## 3. Telegram Customer — عميل الشركة

ده لا يعمل login عندك.
هو فقط:

```text
يفتح Telegram
يكلم بوت الشركة
البوت يرد عليه
النظام يخزن المحادثة
```

---

# أهم قواعد ممنوع تتكسر

دي لازم تحطها للـ Agent في أول البرومبت:

```text
1. Do not rewrite the existing RAG pipeline.
2. Keep users/projects/assets/chunks as the core knowledge-base model.
3. Keep POST /projects/{project_id}/query for web/admin testing.
4. Do not use global bot_config.json for product behavior anymore.
5. Do not use BOT_API_USERNAME/AUTH_ADMIN_USERNAME service account for customer Telegram queries.
6. Every Telegram message must resolve through bot_integrations.
7. Never auto-select another project if the linked project fails.
8. Company users see only their own data by owner_id.
9. Platform owner sees all data only through /admin/* endpoints.
10. Do not expose internal document names/similarity scores to Telegram customers unless enabled.
```

الكود الحالي أصلًا موثق إن Telegram bot دلوقتي بيقرأ `active_project_id` من `uploads/config/bot_config.json` وبيستخدم `/auth/login` ثم `/projects/{project_id}/query`، وده اللي هنحوّله إلى legacy/demo فقط. 

---

# Database Plan — أقل تغييرات تسمح بالمنتج

## عدّل جدول `users`

أضف أعمدة بسيطة:

```sql
ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'company_admin';
ALTER TABLE users ADD COLUMN company_name VARCHAR(255);
ALTER TABLE users ADD COLUMN company_website VARCHAR(255);
ALTER TABLE users ADD COLUMN account_status VARCHAR(30) NOT NULL DEFAULT 'active';
```

القيم:

```text
role:
- platform_owner
- company_admin

account_status:
- active
- suspended
```

**مهم:** أول user أو user معين يتم ترقيته يدويًا إلى:

```text
platform_owner
```

---

## أضف جدول `bot_integrations`

ده بديل `bot_config.json` في منطق المنتج.

```sql
CREATE TABLE bot_integrations (
    id SERIAL PRIMARY KEY,

    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    platform VARCHAR(30) NOT NULL DEFAULT 'telegram',

    name VARCHAR(150),
    telegram_bot_id BIGINT UNIQUE,
    telegram_bot_username VARCHAR(255),
    telegram_bot_display_name VARCHAR(255),

    bot_token_encrypted TEXT NOT NULL,
    bot_token_hash VARCHAR(255) NOT NULL UNIQUE,
    webhook_secret VARCHAR(255) NOT NULL UNIQUE,

    status VARCHAR(30) NOT NULL DEFAULT 'active',
    last_error TEXT,

    welcome_message TEXT,
    fallback_message TEXT,
    handoff_message TEXT,

    language VARCHAR(10) DEFAULT 'ar',
    tone VARCHAR(50) DEFAULT 'professional',

    show_sources_to_customer BOOLEAN DEFAULT false,
    human_handoff_enabled BOOLEAN DEFAULT true,
    collect_contact_enabled BOOLEAN DEFAULT false,

    created_by_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## أضف جدول `telegram_customers`

```sql
CREATE TABLE telegram_customers (
    id SERIAL PRIMARY KEY,

    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_integration_id INTEGER NOT NULL REFERENCES bot_integrations(id) ON DELETE CASCADE,

    telegram_user_id BIGINT,
    chat_id BIGINT NOT NULL,

    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(20),

    is_blocked BOOLEAN DEFAULT false,

    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(bot_integration_id, chat_id)
);
```

---

## أضف جدول `conversations`

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,

    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_integration_id INTEGER NOT NULL REFERENCES bot_integrations(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES telegram_customers(id) ON DELETE CASCADE,

    platform VARCHAR(30) NOT NULL DEFAULT 'telegram',

    status VARCHAR(30) NOT NULL DEFAULT 'open',
    assigned_to_user_id INTEGER REFERENCES users(id),

    last_message_text TEXT,
    last_message_at TIMESTAMP,
    unread_count INTEGER DEFAULT 0,

    needs_human BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## أضف جدول `conversation_messages`

```sql
CREATE TABLE conversation_messages (
    id SERIAL PRIMARY KEY,

    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    sender_type VARCHAR(30) NOT NULL,
    sender_user_id INTEGER REFERENCES users(id),

    telegram_message_id BIGINT,

    content TEXT NOT NULL,

    answer_sources_json JSONB,
    context_used INTEGER,
    confidence_score FLOAT,

    raw_payload_json JSONB,

    status VARCHAR(30) DEFAULT 'sent',
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Indexes مهمة

```sql
CREATE INDEX ix_users_role ON users(role);
CREATE INDEX ix_users_account_status ON users(account_status);

CREATE INDEX ix_bot_integrations_owner_id ON bot_integrations(owner_id);
CREATE INDEX ix_bot_integrations_project_id ON bot_integrations(project_id);
CREATE INDEX ix_bot_integrations_status ON bot_integrations(status);

CREATE INDEX ix_telegram_customers_owner_id ON telegram_customers(owner_id);
CREATE INDEX ix_telegram_customers_bot_chat ON telegram_customers(bot_integration_id, chat_id);

CREATE INDEX ix_conversations_owner_status ON conversations(owner_id, status);
CREATE INDEX ix_conversations_bot_id ON conversations(bot_integration_id);
CREATE INDEX ix_conversations_project_id ON conversations(project_id);
CREATE INDEX ix_conversations_last_message_at ON conversations(last_message_at);

CREATE INDEX ix_conversation_messages_owner_id ON conversation_messages(owner_id);
CREATE INDEX ix_conversation_messages_conversation_created ON conversation_messages(conversation_id, created_at);
```

---

# Backend Plan

## Files to add

```text
backend/routes/admin.py
backend/routes/bot_integrations.py
backend/routes/telegram_webhook.py
backend/routes/conversations.py

backend/services/admin_service.py
backend/services/bot_integration_service.py
backend/services/telegram_api_service.py
backend/services/telegram_webhook_service.py
backend/services/conversation_service.py
backend/services/customer_bot_query_service.py
backend/services/token_encryption_service.py
```

## Files to modify

```text
backend/database/models.py
backend/main.py
backend/security/auth.py
backend/routes/bot_config.py
AGENTS.md
backend/ENDPOINTS.md
```

---

# Backend Implementation Details

## 1. `backend/security/auth.py`

أضف helpers:

```python
def require_platform_owner(current_user):
    if current_user.role != "platform_owner":
        raise HTTPException(status_code=403, detail="Platform owner access required")
    return current_user


def require_active_company(current_user):
    if current_user.account_status != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    return current_user
```

ولو عندك dependency style:

```python
async def get_platform_owner_user(
    current_user: User = Depends(get_current_db_user),
):
    if current_user.role != "platform_owner":
        raise HTTPException(status_code=403, detail="Platform owner access required")
    return current_user
```

---

## 2. `backend/routes/admin.py`

دي endpoints ليك أنت فقط.

```text
GET /admin/companies
GET /admin/companies/{company_id}
GET /admin/companies/{company_id}/projects
GET /admin/companies/{company_id}/bot-integrations
GET /admin/companies/{company_id}/conversations
GET /admin/conversations/{conversation_id}
GET /admin/conversations/{conversation_id}/messages
GET /admin/stats
POST /admin/companies/{company_id}/suspend
POST /admin/companies/{company_id}/activate
```

كل endpoint لازم يبدأ بـ:

```python
current_user = Depends(get_platform_owner_user)
```

أو أي dependency مشابه.

**ممنوع** تستخدم `/projects` العادية عشان تعرض كل الشركات.
اعمل `/admin/*` منفصلة.

---

## 3. `backend/routes/bot_integrations.py`

Endpoints للشركة:

```text
GET    /bot-integrations
POST   /bot-integrations
GET    /bot-integrations/{id}
PUT    /bot-integrations/{id}
DELETE /bot-integrations/{id}

POST   /bot-integrations/{id}/test
POST   /bot-integrations/{id}/enable
POST   /bot-integrations/{id}/disable
POST   /bot-integrations/{id}/rotate-token
GET    /bot-integrations/{id}/readiness
```

قواعد مهمة:

```text
GET /bot-integrations:
- company_admin يشوف bots بتاعته فقط: owner_id = current_user.id
- platform_owner لا يستخدم هذا endpoint لكل الشركات؛ يستخدم /admin

POST /bot-integrations:
- validate project_id belongs to current_user.id
- validate Telegram token using getMe
- encrypt token
- save bot_id, username, display_name
- generate webhook_secret
- register webhook
```

---

## 4. `backend/services/telegram_api_service.py`

وظائف:

```python
validate_token_and_get_me(bot_token)
set_webhook(bot_token, webhook_url)
delete_webhook(bot_token)
send_message(bot_token, chat_id, text)
```

مهم:

```text
لا تطبع bot_token في logs
لا ترجع bot_token في response
```

---

## 5. `backend/services/token_encryption_service.py`

وظائف:

```python
encrypt_secret(value: str) -> str
decrypt_secret(value: str) -> str
hash_secret(value: str) -> str
```

أضف env:

```text
BOT_TOKEN_ENCRYPTION_KEY=
PUBLIC_WEBHOOK_BASE_URL=
```

لو مفيش encryption key، fail عند إنشاء bot integration.

---

## 6. `backend/routes/telegram_webhook.py`

Endpoint:

```text
POST /telegram/webhook/{integration_id}/{webhook_secret}
```

Flow:

```text
1. load BotIntegration by integration_id + webhook_secret
2. if not found → 404
3. if status != active → return 200 but do nothing or send disabled message
4. parse Telegram update
5. ignore non-text messages for now
6. create/find TelegramCustomer by bot_integration_id + chat_id
7. if customer is_blocked → stop
8. create/find open Conversation for customer + bot
9. save customer message
10. call CustomerBotQueryService
11. save bot reply
12. send reply to Telegram
13. update conversation.last_message_text/last_message_at/unread_count/status
```

---

## 7. `backend/services/customer_bot_query_service.py`

ده أهم service.

لازم يستخدم الـ RAG core الحالي من غير ما Telegram يعمل login كـ admin.

Pseudo:

```python
async def answer_customer_message(
    db,
    integration: BotIntegration,
    conversation: Conversation,
    message_text: str,
):
    owner_id = integration.owner_id
    project_id = integration.project_id

    # call existing query stack internally
    # use QueryController / QueryService / AnswerService
    # keep owner_id + project_id scoping

    result = await QueryController.answer_query(
        db=db,
        project_id=project_id,
        query=message_text,
        owner_id=owner_id,
        top_k=...
    )

    customer_text = result.answer

    if not integration.show_sources_to_customer:
        do_not_append_sources_to_customer_text()

    return {
        "answer": customer_text,
        "sources": result.sources,
        "context_used": result.context_used,
        "confidence_score": ...
    }
```

مهم جدًا:
`answer_sources_json` يتخزن داخليًا في `conversation_messages`، لكن لا يظهر للعميل إلا لو `show_sources_to_customer = true`.

---

## 8. `backend/routes/conversations.py`

Company endpoints:

```text
GET /conversations
GET /conversations/{id}
GET /conversations/{id}/messages

POST /conversations/{id}/reply
POST /conversations/{id}/resolve
POST /conversations/{id}/escalate
POST /conversations/{id}/assign
POST /conversations/{id}/block-customer
```

قواعد:

```text
company_admin:
- يشوف فقط conversations.owner_id = current_user.id

platform_owner:
- لا يستخدم هذه endpoints لكل الشركات
- يستخدم /admin/conversations
```

Manual reply:

```text
POST /conversations/{id}/reply
→ decrypt bot token
→ send message to Telegram customer chat_id
→ save message sender_type='agent'
```

---

## 9. `backend/routes/bot_config.py`

خليها legacy.

إما:

```text
تعطّلها تدريجيًا
```

أو:

```text
ترجع warning: "Legacy bot config is deprecated. Use /bot-integrations."
```

لكن **ممنوع** أي product logic يعتمد على:

```text
uploads/config/bot_config.json
active_project_id
```

لأن runtime config الحالي موثق إنه موجود في `uploads/config/app_config.json` و `uploads/config/bot_config.json`، لكن ده مناسب runtime/demo، مش منطق SaaS multi-company. 

---

# Frontend Plan

## Files to modify

```text
frontend/app.js
frontend/index.html
frontend/styles.css
```

الكود الحالي موثق إن `frontend/app.js` هو المسؤول عن dashboard behavior وauth state وprojects/documents/query/config screens، فالتعديلات كلها ممكن تبدأ منه بدل فتح ملفات كتير. 

---

## Sidebar الجديد

أضف navigation items:

```text
Dashboard
Projects / Knowledge Bases
Smart Chat
Telegram Bots
Conversations
Admin Console   يظهر فقط لو role = platform_owner
AI Settings
Account Settings
```

---

## 1. Telegram Bots Page

بدل bot config الحالي.

تعرض:

```text
Bot Name
Telegram Username
Linked Project
Status
Messages Today
Last Error
Actions
```

Actions:

```text
Test
Edit
Disable/Enable
Rotate Token
Delete
View Conversations
```

---

## 2. Add/Edit Bot Form

Fields:

```text
Bot Name
Telegram Bot Token
Linked Project
Language
Tone
Welcome Message
Fallback Message
Handoff Message
Show sources to customers?
Human handoff enabled?
Collect contact enabled?
```

Important UX:

```text
الشركة تدخل Bot Token فقط.
النظام يجيب Bot ID و Username تلقائيًا.
بعد الحفظ، لا تعرض التوكن مرة ثانية.
```

---

## 3. Conversations Inbox

Table:

```text
Customer
Telegram username
Bot
Project
Status
Needs Human
Unread Count
Last Message
Last Activity
```

Filters:

```text
All
Open
Escalated
Resolved
Blocked
By Bot
By Project
Unread only
```

---

## 4. Conversation Detail

تعرض:

```text
Full message history
customer messages
bot replies
agent replies
internal sources
context_used
confidence_score
raw errors if any
```

Actions:

```text
Reply manually
Resolve
Escalate
Assign
Block customer
```

مهم:
الـ sources تظهر للشركة داخليًا فقط.

---

## 5. Project Detail Enhancement

في صفحة كل Project أضف section:

```text
Linked Telegram Bots
```

وتعرض:

```text
@bot_username
status
messages count
view conversations
```

وزر:

```text
Connect Telegram Bot
```

---

## 6. Admin Console Page

تظهر فقط لو:

```text
currentUser.role === "platform_owner"
```

تعرض:

```text
Companies
Projects
Bots
Conversations
Usage
Errors
```

Admin views:

```text
All Companies
Company Detail
Company Projects
Company Bots
Company Conversations
Global Conversations
Platform Stats
```

---

# Testing Plan

## Backend tests / smoke tests

أضف أو عدّل `tools/test_all.py` بحيث يختبر:

```text
1. signup/login company user
2. create project
3. upload/process document
4. create bot integration with fake/mock Telegram validation
5. simulate Telegram webhook message
6. verify telegram_customer created
7. verify conversation created
8. verify customer message saved
9. verify bot reply saved
10. company can list own conversations
11. another company cannot access them
12. platform_owner can list all companies
13. platform_owner can view company conversations
14. bot never auto-selects a different project
15. legacy bot_config is not used
```

---

# Implementation Order للـ Agent

خليه يمشي بالترتيب ده عشان ما يصرفش توكنز:

## Step 0 — Read only these first

```bash
rg -n "class User|class Project|class Asset|class Chunk" backend/database/models.py
rg -n "get_current_db_user|owner_id|role|require" backend/security backend/routes
rg -n "query_project|answer_query|search_similar_chunks|generate_answer" backend
rg -n "bot_config|active_project_id|BOT_API_USERNAME|AUTH_ADMIN_USERNAME" backend telegram_bot frontend
rg -n "include_router" backend/main.py
```

ما يفتحش المشروع كله.

---

## Step 1 — DB models + migration

Modify:

```text
backend/database/models.py
backend/alembic/versions/<new_revision>.py
```

Add:

```text
User.role
User.company_name
User.company_website
User.account_status

BotIntegration
TelegramCustomer
Conversation
ConversationMessage
```

---

## Step 2 — Security helpers

Modify:

```text
backend/security/auth.py
```

Add:

```text
get_platform_owner_user
require company active check
```

---

## Step 3 — Bot integrations backend

Add:

```text
backend/routes/bot_integrations.py
backend/services/bot_integration_service.py
backend/services/telegram_api_service.py
backend/services/token_encryption_service.py
```

Mount in:

```text
backend/main.py
```

---

## Step 4 — Telegram webhook backend

Add:

```text
backend/routes/telegram_webhook.py
backend/services/telegram_webhook_service.py
backend/services/customer_bot_query_service.py
backend/services/conversation_service.py
```

Mount in:

```text
backend/main.py
```

---

## Step 5 — Conversations backend

Add:

```text
backend/routes/conversations.py
backend/services/conversation_service.py
```

Mount in:

```text
backend/main.py
```

---

## Step 6 — Admin backend

Add:

```text
backend/routes/admin.py
backend/services/admin_service.py
```

Mount in:

```text
backend/main.py
```

---

## Step 7 — Legacy cleanup

Modify:

```text
backend/routes/bot_config.py
telegram_bot/handlers.py
telegram_bot/bot.py
```

Do one of these:

```text
Option A:
Keep telegram_bot folder as local/demo only and document it as deprecated.

Option B:
Stop using it in product flow and move Telegram receiving to backend webhook.
```

Recommended:

```text
Use backend webhook for product.
Keep telegram_bot only as legacy/dev demo.
```

---

## Step 8 — Frontend

Modify:

```text
frontend/app.js
frontend/index.html
frontend/styles.css
```

Add:

```text
Telegram Bots page
Create/Edit Bot form
Conversations inbox
Conversation detail
Admin Console
Project linked bots section
```

---

## Step 9 — Docs

Update:

```text
AGENTS.md
backend/ENDPOINTS.md
README.md
docs/project-graph.md
```

AGENTS.md مهم جدًا لأن المشروع نفسه موصي إن أي structural change يتحدث فيه، وإن الـ Agent يبدأ ب targeted search مش broad file dump. 

---

# Acceptance Criteria نهائية

الـ Agent ما يعتبرش المهمة خلصت إلا لما دول يشتغلوا:

```text
1. Platform owner can see all companies.
2. Platform owner can see all company projects.
3. Platform owner can see all bot integrations.
4. Platform owner can see all conversations/messages.

5. Company admin can see only own projects.
6. Company admin can see only own bot integrations.
7. Company admin can see only own conversations/messages.

8. Company admin can create multiple Telegram bot integrations.
9. Each bot integration links to exactly one project.
10. Bot token is encrypted and never returned in API responses.
11. Telegram webhook resolves bot_integration by integration_id + secret.
12. Telegram customer is created automatically from Telegram update.
13. Conversation is created automatically.
14. Customer message is saved.
15. Bot answer is saved.
16. Bot answer is sent back to Telegram.
17. Bot answers only from linked project.
18. No global active_project_id is used.
19. No service/admin login is used for customer Telegram query.
20. No auto-switch to another project.
21. Sources are hidden from Telegram customers by default.
22. Company dashboard shows conversations.
23. Admin console shows all companies/conversations.
24. Existing web project query still works.
25. Existing upload/process/index flow still works.
```

---

# البرومبت النهائي الجاهز للـ Agent

انسخ ده زي ما هو:

```text
You are implementing the final production architecture for RAGMind as a B2B SaaS Telegram customer-support product.

Read this carefully and do not waste tokens by opening the whole repo. Start with targeted search only.

Current architecture to preserve:
- Existing users/projects/assets/chunks RAG core must remain.
- Existing document upload, processing, chunking, embedding, pgvector/vector search, and answer generation must not be rewritten.
- Existing POST /projects/{project_id}/query remains for web/admin test chat.
- Existing owner_id/project_id scoping must remain intact.
- Current global bot_config.json / active_project_id / service-account Telegram flow is legacy/demo only and must not be used for product behavior.

Product roles:
1. platform_owner:
   - owner of the whole platform.
   - can view all companies/users, projects, bot integrations, conversations, messages, usage, errors.
   - uses /admin/* endpoints only for cross-company access.

2. company_admin:
   - normal authenticated user/company account.
   - can create projects/knowledge bases.
   - can upload documents.
   - can create multiple Telegram bot integrations.
   - can view only own bots/conversations/messages by owner_id.

3. telegram_customer:
   - external Telegram user.
   - does not login to the web app.
   - sends messages to a company Telegram bot.
   - is created automatically from Telegram update.

Implementation rules:
- Do not use global active_project_id for product behavior.
- Do not use BOT_API_USERNAME/AUTH_ADMIN_USERNAME service-account login for customer Telegram messages.
- Every Telegram message must resolve through bot_integrations.
- Each bot integration belongs to one owner_id and one project_id.
- Each company can have many bot integrations.
- Each bot integration links to exactly one project.
- Never auto-select another project if the linked project fails.
- If linked project is invalid/unavailable, mark bot integration status='error' and save last_error.
- Do not expose internal document names/similarity scores to Telegram customers unless show_sources_to_customer=true.
- Store all customer messages and bot replies.
- Company dashboard must show conversations.
- Platform owner admin console must show all companies and their data.

Step 0: Read only these areas first:
- backend/database/models.py
- backend/security/auth.py
- backend/routes/projects.py
- backend/routes/query.py
- backend/controllers/query_controller.py
- backend/services/query_service.py
- backend/services/answer_service.py
- backend/main.py
- frontend/app.js
- telegram_bot/handlers.py only to deprecate/understand legacy behavior

Use these commands first:
rg -n "class User|class Project|class Asset|class Chunk" backend/database/models.py
rg -n "get_current_db_user|owner_id|role|require" backend/security backend/routes
rg -n "query_project|answer_query|search_similar_chunks|generate_answer" backend
rg -n "bot_config|active_project_id|BOT_API_USERNAME|AUTH_ADMIN_USERNAME" backend telegram_bot frontend
rg -n "include_router" backend/main.py

Database changes:
1. Modify User model:
   - role VARCHAR(30) default 'company_admin'
   - company_name VARCHAR(255) nullable
   - company_website VARCHAR(255) nullable
   - account_status VARCHAR(30) default 'active'

2. Add BotIntegration model/table:
   - id
   - owner_id FK users.id
   - project_id FK projects.id
   - platform default 'telegram'
   - name
   - telegram_bot_id unique
   - telegram_bot_username
   - telegram_bot_display_name
   - bot_token_encrypted
   - bot_token_hash unique
   - webhook_secret unique
   - status default 'active'
   - last_error
   - welcome_message
   - fallback_message
   - handoff_message
   - language default 'ar'
   - tone default 'professional'
   - show_sources_to_customer default false
   - human_handoff_enabled default true
   - collect_contact_enabled default false
   - created_by_user_id FK users.id
   - created_at
   - updated_at

3. Add TelegramCustomer model/table:
   - id
   - owner_id FK users.id
   - bot_integration_id FK bot_integrations.id
   - telegram_user_id
   - chat_id
   - username
   - first_name
   - last_name
   - language_code
   - is_blocked default false
   - first_seen_at
   - last_seen_at
   - unique(bot_integration_id, chat_id)

4. Add Conversation model/table:
   - id
   - owner_id FK users.id
   - bot_integration_id FK bot_integrations.id
   - project_id FK projects.id
   - customer_id FK telegram_customers.id
   - platform default 'telegram'
   - status default 'open'
   - assigned_to_user_id FK users.id nullable
   - last_message_text
   - last_message_at
   - unread_count default 0
   - needs_human default false
   - resolved_at
   - created_at
   - updated_at

5. Add ConversationMessage model/table:
   - id
   - owner_id FK users.id
   - conversation_id FK conversations.id
   - sender_type: customer/bot/agent/system/error
   - sender_user_id FK users.id nullable
   - telegram_message_id
   - content
   - answer_sources_json JSONB
   - context_used
   - confidence_score
   - raw_payload_json JSONB
   - status default 'sent'
   - error_message
   - created_at

6. Add Alembic migration with indexes:
   - users.role
   - users.account_status
   - bot_integrations.owner_id
   - bot_integrations.project_id
   - bot_integrations.status
   - telegram_customers.owner_id
   - telegram_customers(bot_integration_id, chat_id)
   - conversations(owner_id, status)
   - conversations.bot_integration_id
   - conversations.project_id
   - conversations.last_message_at
   - conversation_messages.owner_id
   - conversation_messages(conversation_id, created_at)

Backend security:
1. Add get_platform_owner_user dependency in backend/security/auth.py.
2. Add active account check for company users.
3. All /admin/* endpoints require platform_owner.
4. All company endpoints filter by owner_id=current_user.id.

Backend routes to add:
1. backend/routes/admin.py
   - GET /admin/companies
   - GET /admin/companies/{company_id}
   - GET /admin/companies/{company_id}/projects
   - GET /admin/companies/{company_id}/bot-integrations
   - GET /admin/companies/{company_id}/conversations
   - GET /admin/conversations/{conversation_id}
   - GET /admin/conversations/{conversation_id}/messages
   - GET /admin/stats
   - POST /admin/companies/{company_id}/suspend
   - POST /admin/companies/{company_id}/activate

2. backend/routes/bot_integrations.py
   - GET /bot-integrations
   - POST /bot-integrations
   - GET /bot-integrations/{id}
   - PUT /bot-integrations/{id}
   - DELETE /bot-integrations/{id}
   - POST /bot-integrations/{id}/test
   - POST /bot-integrations/{id}/enable
   - POST /bot-integrations/{id}/disable
   - POST /bot-integrations/{id}/rotate-token
   - GET /bot-integrations/{id}/readiness

3. backend/routes/telegram_webhook.py
   - POST /telegram/webhook/{integration_id}/{webhook_secret}

4. backend/routes/conversations.py
   - GET /conversations
   - GET /conversations/{id}
   - GET /conversations/{id}/messages
   - POST /conversations/{id}/reply
   - POST /conversations/{id}/resolve
   - POST /conversations/{id}/escalate
   - POST /conversations/{id}/assign
   - POST /conversations/{id}/block-customer

Backend services to add:
1. AdminService
2. BotIntegrationService
3. TelegramApiService
4. TelegramWebhookService
5. ConversationService
6. CustomerBotQueryService
7. TokenEncryptionService

TelegramApiService:
- validate_token_and_get_me(bot_token)
- set_webhook(bot_token, webhook_url)
- delete_webhook(bot_token)
- send_message(bot_token, chat_id, text)

TokenEncryptionService:
- encrypt_secret
- decrypt_secret
- hash_secret
- Do not log tokens.
- Do not return bot_token in API responses.

BotIntegrationService:
- validate project ownership before linking bot to project.
- validate Telegram token with getMe.
- save telegram_bot_id, username, display_name.
- encrypt token.
- save token hash.
- generate webhook_secret.
- set webhook using PUBLIC_WEBHOOK_BASE_URL.
- readiness check must verify project exists, project has processed documents/chunks, token valid, webhook configured, LLM configured.

TelegramWebhookService:
- receive Telegram update.
- resolve BotIntegration by integration_id and webhook_secret.
- ignore if inactive or disabled.
- parse chat_id, telegram_user_id, username, first_name, last_name, message text.
- create/find TelegramCustomer by bot_integration_id + chat_id.
- if customer blocked, do not answer.
- create/find open Conversation.
- save customer ConversationMessage.
- call CustomerBotQueryService.
- save bot ConversationMessage with answer_sources_json/context_used/confidence_score.
- send answer to Telegram using decrypted bot token.
- update Conversation last_message_text, last_message_at, unread_count, status.
- on error, save error message and update bot integration last_error.

CustomerBotQueryService:
- Reuse existing QueryController/QueryService/AnswerService.
- Use owner_id = bot_integration.owner_id.
- Use project_id = bot_integration.project_id.
- Do not require Telegram to login.
- Do not use service/admin account.
- Return customer-safe answer.
- Hide sources from customer unless show_sources_to_customer=true.
- Store sources internally in ConversationMessage.answer_sources_json.

Conversations:
- Company endpoints filter by owner_id=current_user.id.
- Manual reply sends Telegram message via bot token and stores sender_type='agent'.
- Resolve/escalate/assign/block update conversation/customer status safely.

Legacy:
- Mark backend/routes/bot_config.py as legacy/deprecated or keep for old UI only.
- No product behavior should depend on uploads/config/bot_config.json.
- telegram_bot folder can remain as legacy local demo, but production flow must use backend webhook.

Frontend:
Modify frontend/app.js, frontend/index.html, frontend/styles.css.

Add navigation:
- Dashboard
- Projects / Knowledge Bases
- Smart Chat
- Telegram Bots
- Conversations
- Admin Console only for platform_owner
- AI Settings
- Account Settings

Add Telegram Bots page:
- List bots with name, username, linked project, status, messages count, last_error.
- Actions: Test, Edit, Disable/Enable, Rotate Token, Delete, View Conversations.

Add Create/Edit Bot form:
- bot name
- bot token
- linked project
- language
- tone
- welcome message
- fallback message
- handoff message
- show sources to customers
- human handoff enabled
- collect contact enabled
Important: user enters bot token only; backend fetches bot id/username automatically. Never display token after save.

Add Conversations Inbox:
- customer
- telegram username
- bot
- project
- status
- needs human
- unread count
- last message
- last activity
Filters: all/open/escalated/resolved/blocked/by bot/by project/unread only.

Add Conversation Detail:
- full message history
- customer messages
- bot replies
- agent replies
- internal sources
- context_used
- confidence_score
- actions: reply manually, resolve, escalate, assign, block customer.

Add Project detail enhancement:
- Linked Telegram Bots section.
- Button: Connect Telegram Bot.

Add Admin Console:
- visible only when currentUser.role === 'platform_owner'
- companies list
- company detail
- company projects
- company bot integrations
- company conversations
- global stats
- suspend/activate company

Update docs:
- AGENTS.md
- backend/ENDPOINTS.md
- README.md
- docs/project-graph.md

Testing:
Update tools/test_all.py or add focused smoke tests:
1. platform_owner can list all companies.
2. company A cannot access company B projects/conversations.
3. company creates project.
4. company creates bot integration linked to own project.
5. bot cannot link to project owned by another company.
6. webhook creates customer/conversation/messages.
7. bot answer is saved.
8. bot reply is sent through TelegramApiService mock.
9. sources hidden by default.
10. no global active_project_id is used.
11. no service/admin login is used for customer query.
12. linked project failure does not auto-select another project.
13. platform_owner can view all conversations.
14. existing /projects/{project_id}/query still works.
15. existing document upload/process/index still works.

Acceptance criteria:
- Platform owner sees all companies/projects/bots/conversations/messages.
- Company sees only own projects/bots/conversations/messages.
- One company can have multiple Telegram bots.
- Each bot is linked to exactly one project.
- Telegram customers are created automatically.
- Every Telegram message and bot reply is stored.
- Customer bot answers only from linked project.
- Company dashboard shows conversations.
- Admin console shows cross-company data.
- Existing RAG core remains working.
- bot_config.json is legacy only.
```

---

# خلاصة التنفيذ

خلي الـ Agent يشتغل بالترتيب ده فقط:

```text
1. DB models + migration
2. security roles
3. bot integrations backend
4. telegram webhook backend
5. conversations backend
6. admin backend
7. frontend bot/conversation/admin pages
8. tests
9. docs/AGENTS update
```

ده هيحقق المنتج كامل بالمنطق اللي أنت عايزه، من غير ما يهدم الـ RAG core الموجود.
