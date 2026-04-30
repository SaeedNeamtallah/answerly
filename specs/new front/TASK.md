# TASK.md — RAGMind Next.js Frontend Migration

> Purpose: give an implementation agent enough exact context to build a new `frontend-next/` app without guessing, without rewriting the FastAPI backend, and without copying the old static UI 1:1.

---

## 0. Current Context The Agent Must Preserve

### Existing product

RAGMind is currently a B2B SaaS RAG platform with:

- FastAPI backend.
- JWT Bearer auth.
- PostgreSQL + pgvector, optional Qdrant.
- Celery background processing for document ingestion/indexing.
- Database-backed Telegram bot integrations.
- Durable conversations/messages.
- Platform admin console APIs.
- Legacy static frontend in `frontend/`.

### Existing frontend problem

The current frontend is static HTML/CSS/Vanilla JS:

```txt
frontend/
  index.html
  login.html
  signup.html
  app.js
```

`frontend/app.js` currently owns too much behavior: API base discovery, auth state, projects, documents, query UI, config, bot settings, conversations, admin/security screens, and DOM manipulation.

Do **not** port this file 1:1. Use it only as behavioral reference when needed.

### Existing backend truths

The backend is source of truth. Do not duplicate or move these responsibilities into Next.js:

- Authentication and authorization.
- Ownership scoping.
- Project/document/query business logic.
- Celery processing/indexing.
- Telegram webhook/customer query processing.
- Token encryption.
- Conversation storage.
- Admin authorization.

### Critical backend rules

Preserve these rules exactly:

1. Ownership comes from JWT-backed `current_user`, not request payloads.
2. Product roles are DB-backed on `users.role`.
3. Default product role is `company_admin`.
4. `PLATFORM_OWNER_USERNAME` promotes matching DB user to `platform_owner`.
5. `/admin/*` routes are for `platform_owner` only.
6. Company users must never see or access Admin Console UI.
7. Company SaaS routes must remain scoped to current user/company.
8. Telegram bot tokens must never be displayed after save.
9. Telegram bot tokens must not be logged or returned to clients.
10. Customer-visible Telegram replies hide sources by default.
11. Internal dashboard may show retrieval/sources metadata.
12. Document processing must go through Celery tasks.
13. Do **not** use legacy `/bot/config` for product behavior.
14. Do **not** use `active_project_id`.
15. Do **not** use the legacy single polling bot flow for new SaaS UI.

---

## 1. Required Documentation Lookup Before Coding

The implementation agent must fetch current docs before coding because framework APIs can change.

If Context7 MCP is available in the agent environment, use it first:

```txt
Use Context7 for:
- Next.js App Router installation/project structure
- shadcn/ui Next.js installation
- TanStack Query v5 React setup
- React Hook Form + Zod resolver
```

If Context7 is not available, use official docs directly:

- Next.js App Router and `create-next-app`
- shadcn/ui Next.js installation
- TanStack Query v5 React installation
- React Hook Form docs
- Zod docs

Do not use blog posts as source of truth for framework setup.

---

## 2. Target Outcome

Build a new frontend app:

```txt
frontend-next/
```

The old `frontend/` must remain intact during migration.

The new frontend must be:

- Next.js App Router.
- TypeScript.
- Tailwind CSS.
- shadcn/ui or equivalent component system.
- Lucide icons.
- TanStack Query for server state.
- React Hook Form + Zod for forms.
- Zustand or React Context for auth/session state.
- Premium B2B SaaS UI.
- Responsive.
- Arabic/English friendly in layout and copy.
- Compatible with existing FastAPI APIs.

---

## 3. Non-Negotiable Prohibitions

Do **not**:

- Delete `frontend/`.
- Rewrite backend business logic in Next.js.
- Use `/bot/config`.
- Use `active_project_id`.
- Use jQuery.
- Use Vanilla DOM manipulation.
- Use a global `app.js` style architecture.
- Hardcode backend IPs.
- Expose Telegram saved tokens.
- Show Admin Console links to `company_admin`.
- Allow `platform_owner` to manually reply in admin conversation detail in v1.
- Use `prompt()` / `confirm()` browser dialogs for product flows.
- Add a fake API response layer to hide missing backend functionality.
- Treat frontend role checks as security. Backend is still source of truth.

---

## 4. Port and Runtime Decisions

### Port choice

The local Docker stack already uses Grafana on `localhost:3000`.

Therefore run Next.js dev server on `3001`:

```json
{
  "scripts": {
    "dev": "next dev -p 3001",
    "build": "next build",
    "start": "next start -p 3001",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  }
}
```

### Environment

Create:

```txt
frontend-next/.env.local.example
```

Content:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Also update root `.env.example` CORS if needed:

```env
CORS_ORIGINS=["http://localhost:3001", "http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]
```

Reason: Next app runs on `3001`, old static frontend still uses `8080`, Grafana uses `3000`.

---

## 5. Target Route Structure

Create this route structure exactly:

```txt
frontend-next/src/app/
  layout.tsx
  globals.css
  providers.tsx
  not-found.tsx

  (auth)/
    login/
      page.tsx
    signup/
      page.tsx

  (company)/
    layout.tsx
    dashboard/
      page.tsx
    onboarding/
      page.tsx
    knowledge-bases/
      page.tsx
      [projectId]/
        page.tsx
    smart-chat/
      page.tsx
    telegram-bots/
      page.tsx
      [botId]/
        page.tsx
    conversations/
      page.tsx
      [conversationId]/
        page.tsx
    ai-settings/
      page.tsx
    account/
      page.tsx

  (admin)/
    admin/
      layout.tsx
      page.tsx
      companies/
        page.tsx
        [companyId]/
          page.tsx
      conversations/
        page.tsx
        [conversationId]/
          page.tsx
      bots/
        page.tsx
      errors/
        page.tsx
      stats/
        page.tsx

  forbidden/
    page.tsx
```

---

## 6. Target Source Structure

Create this structure:

```txt
frontend-next/src/
  app/
  components/
    layout/
      AppShell.tsx
      Sidebar.tsx
      Topbar.tsx
      RoleGuard.tsx
      PageHeader.tsx
      MobileNav.tsx

    ui/
      # shadcn/ui components generated here

    shared/
      MetricCard.tsx
      StatusBadge.tsx
      DataTable.tsx
      EmptyState.tsx
      LoadingState.tsx
      ErrorState.tsx
      ConfirmDialog.tsx
      DangerZone.tsx
      FormSection.tsx
      ReadinessChecklist.tsx
      BackendUnavailableBanner.tsx

    dashboard/
      SetupChecklist.tsx
      BotHealthPanel.tsx
      RecentConversations.tsx
      KnowledgeBaseReadiness.tsx

    knowledge-bases/
      KnowledgeBaseCard.tsx
      KnowledgeBaseTable.tsx
      KnowledgeBaseFormDialog.tsx
      DocumentsTable.tsx
      UploadDocumentCard.tsx
      TestChatPanel.tsx
      LinkedBotsPanel.tsx

    bots/
      BotCard.tsx
      BotTable.tsx
      BotFormDrawer.tsx
      BotReadinessChecklist.tsx
      RotateTokenDialog.tsx

    conversations/
      ConversationList.tsx
      ConversationThread.tsx
      ConversationMetadataPanel.tsx
      ReplyComposer.tsx
      ConversationFilters.tsx
      MessageBubble.tsx
      SourceMetadataPanel.tsx

    admin/
      AdminMetricCards.tsx
      CompaniesTable.tsx
      CompanyDetailTabs.tsx
      AdminConversationsTable.tsx
      AdminBotsTable.tsx
      AdminErrorsFeed.tsx

  lib/
    api/
      client.ts
      health.ts
      auth.ts
      projects.ts
      documents.ts
      query.ts
      botIntegrations.ts
      conversations.ts
      admin.ts
      config.ts

    auth/
      session.ts
      permissions.ts
      redirects.ts

    types/
      auth.ts
      project.ts
      document.ts
      query.ts
      bot.ts
      conversation.ts
      admin.ts
      config.ts
      common.ts

    utils/
      cn.ts
      formatters.ts
      dates.ts
      status.ts

  store/
    auth-store.ts
```

---

## 7. API Mapping

Use `NEXT_PUBLIC_API_BASE_URL` and the existing backend.

### Auth

```txt
POST /auth/login
POST /auth/signup
GET  /auth/me
POST /auth/change-password
```

### Health

```txt
GET /health
GET /health/live
```

### Projects / Knowledge Bases

Treat backend projects as frontend “knowledge bases”.

```txt
GET    /projects/
POST   /projects/
GET    /projects/{id}
PUT    /projects/{id}
DELETE /projects/{id}
GET    /projects/{id}/stats
POST   /projects/{id}/index
```

### Documents

```txt
GET    /projects/{project_id}/documents
POST   /projects/{project_id}/documents
POST   /documents/{asset_id}/process
POST   /documents/{asset_id}/process-and-index
DELETE /documents/{asset_id}
GET    /tasks/{task_id}
```

### Query / Smart Chat

```txt
POST /projects/{project_id}/query
```

### Bot Integrations

```txt
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

### Conversations

```txt
GET  /conversations
GET  /conversations/{id}
GET  /conversations/{id}/messages
POST /conversations/{id}/reply
POST /conversations/{id}/resolve
POST /conversations/{id}/escalate
POST /conversations/{id}/assign
POST /conversations/{id}/block-customer
```

### Admin

```txt
GET  /admin/overview
GET  /admin/stats
GET  /admin/companies
GET  /admin/companies/{company_id}
GET  /admin/companies/{company_id}/projects
GET  /admin/companies/{company_id}/bot-integrations
GET  /admin/companies/{company_id}/conversations
GET  /admin/bot-integrations
GET  /admin/conversations
GET  /admin/conversations/{conversation_id}
GET  /admin/conversations/{conversation_id}/messages
POST /admin/companies/{company_id}/activate
POST /admin/companies/{company_id}/suspend
POST /admin/companies/{company_id}/block
```

### Config / AI Settings

```txt
GET  /config/providers
POST /config/providers
```

Important: for v1, make `/ai-settings` visible to `platform_owner` only unless backend proves config is per-company.

---

## 8. Global Type Conventions

Create conservative types based on actual response shapes. Do not overfit.

All entities should tolerate optional backend fields:

```ts
export type ApiId = number | string;

export interface ApiListResponse<T> {
  items?: T[];
  data?: T[];
  results?: T[];
  total?: number;
}
```

For list endpoints, write normalizers that accept:

- array directly
- `{items: []}`
- `{data: []}`
- `{results: []}`

Never crash page rendering because the backend response uses a slightly different envelope.

---

## 9. Shared API Client Requirements

Create:

```txt
frontend-next/src/lib/api/client.ts
```

Must implement:

```ts
export class ApiError extends Error {
  status: number;
  detail?: unknown;
}

export async function apiRequest<T>(
  path: string,
  options?: RequestInit & { auth?: boolean }
): Promise<T>;
```

Rules:

1. Base URL comes from `process.env.NEXT_PUBLIC_API_BASE_URL`.
2. Default base URL is `http://localhost:8000`.
3. Add `Authorization: Bearer <token>` for authenticated requests.
4. Token comes from auth store/session helper.
5. For JSON body, set `Content-Type: application/json`.
6. For `FormData`, do not set `Content-Type`.
7. On `401`, clear auth session and redirect to `/login`.
8. On `403`, throw `ApiError(403)`; page renders forbidden state.
9. On network failure, throw `ApiError(0, "Backend unavailable")`.
10. Do not swallow backend errors.
11. Do not hardcode endpoints in pages. Use feature API modules.

---

## 10. Auth Session Requirements

Create:

```txt
frontend-next/src/store/auth-store.ts
frontend-next/src/lib/auth/session.ts
frontend-next/src/lib/auth/permissions.ts
frontend-next/src/lib/auth/redirects.ts
```

Because the backend currently uses Bearer token flow, store the token in localStorage for this migration round.

Long-term HttpOnly cookie auth is out of scope.

### Session fields

```ts
interface AuthSession {
  accessToken: string | null;
  currentUser: CurrentUser | null;
  role: "company_admin" | "platform_owner" | string | null;
  isHydrated: boolean;
}
```

### Redirect logic

```txt
not logged in + protected route -> /login
company_admin + /admin/* -> /forbidden or /dashboard
platform_owner after login -> /admin
company_admin after login -> /dashboard
guest visiting /login while authenticated -> role default route
```

### Role rules

```ts
export function isPlatformOwner(user: CurrentUser | null): boolean;
export function isCompanyAdmin(user: CurrentUser | null): boolean;
export function canAccessAdmin(user: CurrentUser | null): boolean;
export function canAccessCompanyWorkspace(user: CurrentUser | null): boolean;
```

---

## 11. UI State Requirements For Every Main Page

Every main page must include:

- Loading state.
- Empty state.
- Error state.
- Success feedback.
- Saving/disabled state for mutations.
- Confirmation before delete/block/suspend.
- Backend unavailable state.
- 401 redirect handling.
- 403 forbidden handling.

Do not leave blank white pages.

---

## 12. Design System

Visual direction:

```txt
Enterprise SaaS
white/slate background
navy/indigo primary
emerald success
amber warning
red danger
rounded cards
soft shadows
clear typography
RTL/LTR ready
```

Use Tailwind tokens:

```txt
background: slate-50
card: white
border: slate-200
primary: indigo/navy
success: emerald
warning: amber
danger: red
neutral: slate
```

Use Lucide icons consistently.

Use shadcn/ui components for:

```txt
button
card
badge
dialog
sheet
tabs
table
input
textarea
select
dropdown-menu
separator
skeleton
alert
form
label
sonner/toast
scroll-area
avatar
```

---

# Implementation Tasks

## Phase 0 — Preflight and Documentation

### T000 — Read repo guidance before coding — done

**Files to inspect:**

```txt
AGENTS.md
README.md
backend/ENDPOINTS.md
backend/routes/auth.py
backend/routes/projects.py
backend/routes/documents.py
backend/routes/query.py
backend/routes/bot_integrations.py
backend/routes/conversations.py
backend/routes/admin_console.py
backend/routes/app_config.py
frontend/app.js
```

**Do:**

- Confirm endpoint paths and payload names.
- Confirm auth response shape.
- Confirm `/auth/me` response shape.
- Confirm bot integration model fields.
- Confirm conversation message response fields.
- Confirm admin console route names.

**Do not:**

- Start broad file reading.
- Modify backend.
- Delete old frontend.

**Acceptance check:**

- Agent has a short local note of verified request/response fields before implementation.

---

### T001 — Fetch framework docs with Context7 — done

**Do:**

Use Context7 MCP if available:

```txt
Resolve docs for:
- Next.js App Router
- shadcn/ui Next.js install
- TanStack Query v5 React
- React Hook Form
- Zod
```

If Context7 is unavailable, use official docs manually.

**Acceptance check:**

- Agent does not use outdated Next.js Pages Router patterns.
- Agent uses App Router and TypeScript.

---

## Phase 1 — Bootstrap `frontend-next`

### T010 — Create Next.js app — done

**Create:**

```txt
frontend-next/
```

**Command:**

```bash
pnpm create next-app@latest frontend-next --typescript --eslint --app --src-dir --import-alias "@/*"
```

If using npm:

```bash
npx create-next-app@latest frontend-next --typescript --eslint --app --src-dir --import-alias "@/*"
```

**Then set scripts in `frontend-next/package.json`:**

```json
{
  "dev": "next dev -p 3001",
  "build": "next build",
  "start": "next start -p 3001",
  "lint": "next lint",
  "typecheck": "tsc --noEmit"
}
```

**Acceptance check:**

```bash
cd frontend-next
pnpm dev
```

opens on `http://localhost:3001`.

---

### T011 — Install dependencies — done

**Install:**

```bash
pnpm add @tanstack/react-query zustand zod react-hook-form @hookform/resolvers lucide-react clsx tailwind-merge date-fns
pnpm add sonner
```

**Install shadcn/ui:**

```bash
pnpm dlx shadcn@latest init
```

Choose:

```txt
Style: New York or Default
Base color: Slate
CSS variables: yes
```

Add components:

```bash
pnpm dlx shadcn@latest add button card badge dialog sheet tabs table input textarea select dropdown-menu separator skeleton alert form label scroll-area avatar
```

**Acceptance check:**

```bash
pnpm typecheck
pnpm build
```

---

### T012 — Configure env — done

**Create:**

```txt
frontend-next/.env.local.example
frontend-next/.env.local
```

**Content:**

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Modify root `.env.example`:**

Add `http://localhost:3001` to `CORS_ORIGINS`.

**Acceptance check:**

- FastAPI accepts requests from `http://localhost:3001`.

---

### T013 — Create app providers — done

**Create:**

```txt
frontend-next/src/app/providers.tsx
```

**Implement:**

- `QueryClientProvider`
- `Sonner` toaster
- auth hydration wrapper if needed

**Modify:**

```txt
frontend-next/src/app/layout.tsx
```

Wrap children in `<Providers>`.

**Acceptance check:**

- App renders with no hydration crash.
- TanStack Query dev/runtime works.

---

## Phase 2 — Shared API and Types

### T020 — Create API client — done

**Create:**

```txt
frontend-next/src/lib/api/client.ts
```

**Implement:**

- `ApiError`
- `apiRequest<T>()`
- token injection
- `FormData` support
- 401 handling
- 403 handling
- network error handling

**Acceptance check:**

- Calling `/health` works without token.
- Calling `/auth/me` without token gives clean 401 handling.

---

### T021 — Create health API — done

**Create:**

```txt
frontend-next/src/lib/api/health.ts
```

**Functions:**

```ts
export async function getHealth(): Promise<HealthResponse>;
export async function getLiveHealth(): Promise<unknown>;
```

**Use endpoints:**

```txt
GET /health
GET /health/live
```

**Acceptance check:**

- Login page shows backend available/unavailable.

---

### T022 — Create type files — done

**Create:**

```txt
frontend-next/src/lib/types/common.ts
frontend-next/src/lib/types/auth.ts
frontend-next/src/lib/types/project.ts
frontend-next/src/lib/types/document.ts
frontend-next/src/lib/types/query.ts
frontend-next/src/lib/types/bot.ts
frontend-next/src/lib/types/conversation.ts
frontend-next/src/lib/types/admin.ts
frontend-next/src/lib/types/config.ts
```

**Rules:**

- Use optional fields where backend shape is uncertain.
- Use string union for known statuses but allow `string`.
- Avoid `any`; use `unknown` when truly unknown.

**Acceptance check:**

```bash
pnpm typecheck
```

passes.

---

### T023 — Create API modules — done

**Create:**

```txt
frontend-next/src/lib/api/auth.ts
frontend-next/src/lib/api/projects.ts
frontend-next/src/lib/api/documents.ts
frontend-next/src/lib/api/query.ts
frontend-next/src/lib/api/botIntegrations.ts
frontend-next/src/lib/api/conversations.ts
frontend-next/src/lib/api/admin.ts
frontend-next/src/lib/api/config.ts
```

**Required exports:**

#### `auth.ts`

```ts
login(payload)
signup(payload)
getMe()
changePassword(payload)
```

#### `projects.ts`

```ts
listProjects()
createProject(payload)
getProject(id)
updateProject(id, payload)
deleteProject(id)
getProjectStats(id)
reindexProject(id)
```

#### `documents.ts`

```ts
listDocuments(projectId)
uploadDocument(projectId, file)
processDocument(assetId)
processAndIndexDocument(assetId)
deleteDocument(assetId)
getTask(taskId)
```

#### `query.ts`

```ts
askProject(projectId, payload)
```

#### `botIntegrations.ts`

```ts
listBotIntegrations(params?)
createBotIntegration(payload)
getBotIntegration(id)
updateBotIntegration(id, payload)
deleteBotIntegration(id)
testBotIntegration(id)
enableBotIntegration(id)
disableBotIntegration(id)
rotateBotToken(id, payload)
getBotReadiness(id)
```

#### `conversations.ts`

```ts
listConversations(params?)
getConversation(id)
getConversationMessages(id)
replyToConversation(id, payload)
resolveConversation(id)
escalateConversation(id)
assignConversation(id)
blockCustomer(id)
```

#### `admin.ts`

```ts
getAdminOverview()
getAdminStats()
listAdminCompanies()
getAdminCompany(companyId)
getAdminCompanyProjects(companyId)
getAdminCompanyBots(companyId)
getAdminCompanyConversations(companyId)
listAdminBots()
listAdminConversations(params?)
getAdminConversation(conversationId)
getAdminConversationMessages(conversationId)
activateCompany(companyId, payload?)
suspendCompany(companyId, payload?)
blockCompany(companyId, payload?)
```

#### `config.ts`

```ts
getProviderConfig()
updateProviderConfig(payload)
```

**Acceptance check:**

- No page uses raw `fetch`.
- All API calls go through these modules.

---

## Phase 3 — Auth, Session, Guards

### T030 — Implement auth store — done

**Create:**

```txt
frontend-next/src/store/auth-store.ts
frontend-next/src/lib/auth/session.ts
```

**Store:**

- `accessToken`
- `currentUser`
- `role`
- `isHydrated`
- `setSession`
- `clearSession`
- `hydrateFromStorage`

**LocalStorage key:**

```txt
ragmind_access_token
```

**Acceptance check:**

- Refreshing page keeps session.
- Logout clears localStorage.

---

### T031 — Implement permissions — done

**Create:**

```txt
frontend-next/src/lib/auth/permissions.ts
frontend-next/src/lib/auth/redirects.ts
```

**Implement:**

```ts
isPlatformOwner(user)
isCompanyAdmin(user)
canAccessAdmin(user)
canAccessCompanyWorkspace(user)
getDefaultRouteForUser(user)
```

**Rules:**

```txt
platform_owner -> /admin
company_admin -> /dashboard
unknown authenticated role -> /dashboard unless backend forbids
```

**Acceptance check:**

- Role functions tolerate missing/optional role fields.

---

### T032 — Create RoleGuard — done

**Create:**

```txt
frontend-next/src/components/layout/RoleGuard.tsx
```

**Props:**

```ts
allowedRoles?: string[];
requireAuth?: boolean;
children: React.ReactNode;
```

**Behavior:**

- Shows loading while auth hydrates.
- Redirects unauthenticated to `/login`.
- Shows `/forbidden` or inline forbidden state on 403 role mismatch.
- Does not expose admin content while loading.

**Acceptance check:**

- `company_admin` cannot see `/admin`.
- Guest cannot see `/dashboard`.

---

### T033 — Implement auth pages — done

**Create:**

```txt
frontend-next/src/app/(auth)/login/page.tsx
frontend-next/src/app/(auth)/signup/page.tsx
```

**Login UI:**

- Split layout.
- Product branding.
- username/email field.
- password field.
- show password toggle.
- backend status.
- link to signup.
- submit button with loading state.

**Login behavior:**

1. POST `/auth/login`.
2. Store access token.
3. GET `/auth/me`.
4. Store user.
5. Redirect:
   - `platform_owner` -> `/admin`
   - `company_admin` -> `/dashboard`

**Signup UI:**

- company_name.
- username/email.
- password.
- confirm_password.
- create workspace button.
- link to login.

**Signup behavior:**

1. Validate confirm password.
2. POST `/auth/signup`.
3. If backend returns token, store it and redirect `/onboarding`.
4. If backend does not return token, redirect `/login` with success message.

**Acceptance check:**

- Login works against existing backend.
- Signup works against existing backend or shows clear backend validation error.
- No `prompt()`.

---

### T034 — Create forbidden page — done

**Create:**

```txt
frontend-next/src/app/forbidden/page.tsx
```

**Acceptance check:**

- Admin access by company user renders a professional forbidden page.

---

## Phase 4 — Layout and Navigation

### T040 — Create layout components — done

**Create:**

```txt
frontend-next/src/components/layout/AppShell.tsx
frontend-next/src/components/layout/Sidebar.tsx
frontend-next/src/components/layout/Topbar.tsx
frontend-next/src/components/layout/PageHeader.tsx
frontend-next/src/components/layout/MobileNav.tsx
```

**Sidebar sections:**

Company workspace:

```txt
Dashboard
Onboarding
Knowledge Bases
Smart Chat
Telegram Bots
Conversations
AI Settings
Account
```

Admin workspace:

```txt
Admin Overview
Companies
Global Conversations
Bots
Errors
Stats
Account
```

**Rules:**

- Admin nav visible only to `platform_owner`.
- Company nav visible to `company_admin`.
- Account visible to authenticated users.

**Acceptance check:**

- `company_admin` sees no Admin Console link.
- `platform_owner` default shell is admin shell.

---

### T041 — Create route group layouts — done

**Create:**

```txt
frontend-next/src/app/(company)/layout.tsx
frontend-next/src/app/(admin)/admin/layout.tsx
```

**Rules:**

- Company layout requires authenticated `company_admin` or authenticated users allowed for company workspace if product allows.
- Admin layout requires `platform_owner`.

**Acceptance check:**

- Direct URL navigation is guarded, not just sidebar-hidden.

---

### T042 — Shared UI components — done

**Create:**

```txt
frontend-next/src/components/shared/MetricCard.tsx
frontend-next/src/components/shared/StatusBadge.tsx
frontend-next/src/components/shared/DataTable.tsx
frontend-next/src/components/shared/EmptyState.tsx
frontend-next/src/components/shared/LoadingState.tsx
frontend-next/src/components/shared/ErrorState.tsx
frontend-next/src/components/shared/ConfirmDialog.tsx
frontend-next/src/components/shared/DangerZone.tsx
frontend-next/src/components/shared/FormSection.tsx
frontend-next/src/components/shared/ReadinessChecklist.tsx
frontend-next/src/components/shared/BackendUnavailableBanner.tsx
```

**Acceptance check:**

- Components are reusable.
- No page repeats generic loading/error/empty UI.

---

## Phase 5 — Company Dashboard and Onboarding

### T050 — Company dashboard page — done

**Create:**

```txt
frontend-next/src/app/(company)/dashboard/page.tsx
frontend-next/src/components/dashboard/SetupChecklist.tsx
frontend-next/src/components/dashboard/BotHealthPanel.tsx
frontend-next/src/components/dashboard/RecentConversations.tsx
frontend-next/src/components/dashboard/KnowledgeBaseReadiness.tsx
```

**Data sources:**

Use TanStack Query to fetch:

```txt
GET /projects/
GET /bot-integrations
GET /conversations
```

Optionally fetch project stats for visible projects:

```txt
GET /projects/{id}/stats
```

**Metric cards:**

- Active Bots.
- Open Conversations.
- Needs Human.
- Messages Today.
- Knowledge Bases.
- Failed Documents.

**If exact metric is unavailable:**

- Derive from available list data.
- Show `—` and helpful tooltip instead of fake numbers.

**Acceptance check:**

- Dashboard works even with empty backend.
- Dashboard does not crash if one panel request fails.

---

### T051 — Onboarding wizard — done

**Create:**

```txt
frontend-next/src/app/(company)/onboarding/page.tsx
```

**Wizard steps:**

1. Company Profile.
2. Create Knowledge Base.
3. Upload Documents.
4. Test AI Chat.
5. Connect Telegram Bot.

**Backend support:**

- Step 1 is display/local-only unless backend profile update endpoint exists.
- Step 2 uses `POST /projects/`.
- Step 3 uses `POST /projects/{project_id}/documents`.
- Step 4 uses `POST /projects/{project_id}/query`.
- Step 5 uses `POST /bot-integrations`.

**Rules:**

- Do not block the user forever if optional step is unavailable.
- Allow “skip for now” where backend support is missing.
- Do not use `/bot/config`.

**Acceptance check:**

- New company admin can reach onboarding after signup.
- User can complete or skip optional steps and go to `/dashboard`.

---

## Phase 6 — Knowledge Bases and RAG Core

### T060 — Knowledge bases list — done

**Create:**

```txt
frontend-next/src/app/(company)/knowledge-bases/page.tsx
frontend-next/src/components/knowledge-bases/KnowledgeBaseCard.tsx
frontend-next/src/components/knowledge-bases/KnowledgeBaseTable.tsx
frontend-next/src/components/knowledge-bases/KnowledgeBaseFormDialog.tsx
```

**Data source:**

```txt
GET /projects/
```

**Actions:**

- New Knowledge Base -> `POST /projects/`.
- Open -> `/knowledge-bases/{projectId}`.
- Upload Documents -> `/knowledge-bases/{projectId}?tab=documents`.
- Test Chat -> `/knowledge-bases/{projectId}?tab=test-chat`.
- Connect Bot -> open BotFormDrawer with project preselected.
- Delete -> `DELETE /projects/{id}` with ConfirmDialog.

**UI:**

- Header.
- Search.
- Filters.
- Card/table toggle if easy.
- Empty state.

**Acceptance check:**

- Projects display as “Knowledge Bases”.
- Delete requires confirmation.
- No raw backend word “project” in user-facing primary navigation unless secondary explanation.

---

### T061 — Knowledge base detail page

**Create:**

```txt
frontend-next/src/app/(company)/knowledge-bases/[projectId]/page.tsx
frontend-next/src/components/knowledge-bases/DocumentsTable.tsx
frontend-next/src/components/knowledge-bases/UploadDocumentCard.tsx
frontend-next/src/components/knowledge-bases/TestChatPanel.tsx
frontend-next/src/components/knowledge-bases/LinkedBotsPanel.tsx
```

**Tabs:**

```txt
Overview
Documents
Test Chat
Linked Bots
Settings
```

**Data:**

```txt
GET /projects/{id}
GET /projects/{id}/stats
GET /projects/{id}/documents
GET /bot-integrations
```

Filter bots by linked project/knowledge base if project id field exists.

**Documents tab actions:**

```txt
Upload -> POST /projects/{project_id}/documents
Process -> POST /documents/{asset_id}/process
Process + Index -> POST /documents/{asset_id}/process-and-index
Delete -> DELETE /documents/{asset_id}
Task polling -> GET /tasks/{task_id}
```

**Test Chat tab:**

```txt
POST /projects/{project_id}/query
```

Show:

- answer
- internal sources
- context/retrieval metadata when available

**Settings tab:**

```txt
PUT /projects/{id}
DELETE /projects/{id}
POST /projects/{id}/index
```

**Acceptance check:**

- Upload/process/query flow works end to end.
- Task status updates until terminal status.
- Query sources are internal-only.
- No page crash if stats endpoint returns partial fields.

---

### T062 — Smart chat page — done

**Create:**

```txt
frontend-next/src/app/(company)/smart-chat/page.tsx
```

**UI:**

- Knowledge base selector from `GET /projects/`.
- Chat thread.
- Question input.
- Answer display.
- Internal sources panel.
- Context metadata panel if available.

**Behavior:**

- Require selected knowledge base.
- Use `POST /projects/{project_id}/query`.
- Keep local chat history in component state.
- Show loading while answer is generating.

**Acceptance check:**

- Smart Chat uses existing query endpoint.
- No nonexistent streaming endpoint is used.

---

## Phase 7 — Telegram Bot Integrations

### T070 — Telegram bots list — done

**Create:**

```txt
frontend-next/src/app/(company)/telegram-bots/page.tsx
frontend-next/src/components/bots/BotCard.tsx
frontend-next/src/components/bots/BotTable.tsx
frontend-next/src/components/bots/BotFormDrawer.tsx
frontend-next/src/components/bots/BotReadinessChecklist.tsx
frontend-next/src/components/bots/RotateTokenDialog.tsx
```

**Data:**

```txt
GET /bot-integrations
GET /projects/
```

**Actions:**

```txt
Create -> POST /bot-integrations
View details -> /telegram-bots/{botId}
Edit -> PUT /bot-integrations/{id}
Test connection -> POST /bot-integrations/{id}/test OR GET /bot-integrations/{id}/readiness
Enable -> POST /bot-integrations/{id}/enable
Disable -> POST /bot-integrations/{id}/disable
Rotate token -> POST /bot-integrations/{id}/rotate-token
Delete -> DELETE /bot-integrations/{id}
View conversations -> /conversations?botId={id}
```

**Important token rule:**

- Token field appears only in create/rotate flows.
- Saved token must never be displayed.
- Do not render token hash.

**Acceptance check:**

- All actions have loading/saving state.
- Token is never displayed after save.
- Readiness shown clearly.

---

### T071 — Bot create/edit drawer — done

**Create/complete:**

```txt
frontend-next/src/components/bots/BotFormDrawer.tsx
```

**Fields:**

Use backend-supported fields first.

Always include:

```txt
bot name
Telegram BotFather token — create only
linked knowledge base
fallback message if supported
show sources to customers if supported
human handoff enabled if supported
```

Only include these if backend schema supports them:

```txt
language
tone
welcome message
handoff message
collect contact enabled
```

**If field not supported:**

- Do not send it.
- Do not show it unless marked “coming soon”.

**Acceptance check:**

- Payload matches backend schema.
- Backend validation errors display next to form/global alert.

---

### T072 — Bot detail page

**Create:**

```txt
frontend-next/src/app/(company)/telegram-bots/[botId]/page.tsx
```

**Data:**

```txt
GET /bot-integrations/{id}
GET /bot-integrations/{id}/readiness
GET /conversations?botId={id} if backend supports filter
```

If filter not supported, fetch conversations and filter client-side.

**Sections:**

- Bot summary.
- `@username`.
- linked knowledge base.
- status.
- webhook status.
- readiness checklist.
- last error.
- recent conversations.
- settings.
- danger zone.

**Actions:**

- Edit settings.
- Test connection/readiness.
- Enable/disable.
- Rotate token.
- Delete.

**Acceptance check:**

- Detail page does not expose saved token.
- Delete requires confirmation.

---

## Phase 8 — Conversations

### T080 — Conversations inbox — done

**Create:**

```txt
frontend-next/src/app/(company)/conversations/page.tsx
frontend-next/src/components/conversations/ConversationList.tsx
frontend-next/src/components/conversations/ConversationThread.tsx
frontend-next/src/components/conversations/ConversationMetadataPanel.tsx
frontend-next/src/components/conversations/ConversationFilters.tsx
frontend-next/src/components/conversations/MessageBubble.tsx
frontend-next/src/components/conversations/SourceMetadataPanel.tsx
frontend-next/src/components/conversations/ReplyComposer.tsx
```

**Data:**

```txt
GET /conversations
GET /conversations/{id}
GET /conversations/{id}/messages
```

**Layout:**

- Left: conversation list.
- Center: selected thread.
- Right: metadata panel.

**Filters:**

- All.
- Open.
- Needs Human.
- Escalated.
- Resolved.
- Blocked.
- Unread.
- By Bot.
- By Knowledge Base.

If backend does not support filter params, filter client-side.

**Acceptance check:**

- Inbox works on empty state.
- Selecting a conversation loads messages and metadata.

---

### T081 — Conversation detail page — done

**Create:**

```txt
frontend-next/src/app/(company)/conversations/[conversationId]/page.tsx
```

**Actions:**

```txt
Reply manually -> POST /conversations/{id}/reply
Resolve -> POST /conversations/{id}/resolve
Escalate -> POST /conversations/{id}/escalate
Assign to me -> POST /conversations/{id}/assign
Block customer -> POST /conversations/{id}/block-customer
```

**Right panel fields:**

- customer info.
- Telegram username.
- bot integration.
- linked knowledge base.
- status.
- needs human.
- internal sources.
- context used.
- confidence score if available.

**Message types:**

Support styling for:

```txt
customer
bot
agent
system
error
```

**Acceptance check:**

- Manual reply works.
- Resolve/escalate/assign/block work.
- Sources metadata shown internally when present.

---

## Phase 9 — AI Settings and Account

### T090 — AI settings page — done

**Create:**

```txt
frontend-next/src/app/(company)/ai-settings/page.tsx
```

**Important permission decision:**

For v1, protect this page as `platform_owner` only unless backend confirms config is per-company.

**Data:**

```txt
GET /config/providers
POST /config/providers
```

**Fields:**

- LLM provider.
- Embedding provider.
- Vector DB provider.
- Retrieval top K.
- Hybrid search.
- Rerank.
- Query rewrite.

**Test provider:**

If no dedicated endpoint exists, do not fake one. Show “Test provider endpoint not available” or run a safe query only after user selects a knowledge base.

**Acceptance check:**

- Company admin cannot mutate global AI settings.
- Save uses authenticated `/config/providers`.

---

### T091 — Account page — done

**Create:**

```txt
frontend-next/src/app/(company)/account/page.tsx
```

**Data:**

```txt
GET /auth/me
POST /auth/change-password
```

**Display:**

- company name if returned.
- company website if returned.
- username/email.
- role badge.
- account status.
- change password form.

**Do not implement profile update unless backend endpoint exists.**

**Acceptance check:**

- Change password works.
- Missing company fields display gracefully.

---

## Phase 10 — Admin Console

### T100 — Admin overview — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/page.tsx
frontend-next/src/components/admin/AdminMetricCards.tsx
```

**Data:**

```txt
GET /admin/overview
GET /admin/stats
```

**Metrics:**

- Total Companies.
- Active Companies.
- Suspended Companies.
- Total Projects.
- Total Bots.
- Total Conversations.
- Messages Today.
- Bot Errors.

**Panels:**

- Recent companies.
- Global bot health.
- Recent errors.
- Recent conversations.
- Usage summary.

**Acceptance check:**

- Page only accessible to `platform_owner`.
- Handles empty/partial admin stats.

---

### T101 — Admin companies list — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/companies/page.tsx
frontend-next/src/components/admin/CompaniesTable.tsx
```

**Data:**

```txt
GET /admin/companies
```

**Actions:**

```txt
View -> /admin/companies/{companyId}
Suspend -> POST /admin/companies/{company_id}/suspend
Activate -> POST /admin/companies/{company_id}/activate
Block -> POST /admin/companies/{company_id}/block
```

**Rules:**

- All destructive/status actions require ConfirmDialog.
- If backend accepts reason payload, include reason textarea.
- If backend does not accept reason, send no body.

**Acceptance check:**

- Company status action invalidates admin company queries.
- No browser `confirm()`.

---

### T102 — Admin company detail

**Create:**

```txt
frontend-next/src/app/(admin)/admin/companies/[companyId]/page.tsx
frontend-next/src/components/admin/CompanyDetailTabs.tsx
```

**Tabs:**

- Overview.
- Projects.
- Bots.
- Conversations.
- Messages.
- Errors.
- Settings.

**Data:**

```txt
GET /admin/companies/{company_id}
GET /admin/companies/{company_id}/projects
GET /admin/companies/{company_id}/bot-integrations
GET /admin/companies/{company_id}/conversations
```

**Messages tab:**

If no direct company messages endpoint exists:

- Show messages through selected conversation drilldown.
- Or show “Open a conversation to view messages”.

Do not fake messages.

**Errors tab:**

If no direct company errors endpoint exists:

- Show bot `last_error`.
- Show failed document statuses if available.
- Show empty state explaining no unified errors endpoint.

**Acceptance check:**

- Detail page renders all tabs without crashing.
- Missing backend endpoints show honest empty/unavailable states.

---

### T103 — Admin global conversations — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/conversations/page.tsx
frontend-next/src/components/admin/AdminConversationsTable.tsx
```

**Data:**

```txt
GET /admin/conversations
```

**Filters:**

- company.
- bot.
- status.
- needs human.
- date range.

If backend does not support filter query params, filter client-side.

**Acceptance check:**

- Table rows link to `/admin/conversations/{conversationId}`.

---

### T104 — Admin conversation detail — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/conversations/[conversationId]/page.tsx
```

**Data:**

```txt
GET /admin/conversations/{conversation_id}
GET /admin/conversations/{conversation_id}/messages
```

**Rule:**

Platform owner is read-only in v1.

**Do not show:**

- Reply composer.
- Resolve button.
- Escalate button.
- Assign button.
- Block customer button.

**Show:**

- Full conversation.
- Messages.
- Sources metadata if present.
- Company.
- Bot.
- Project.
- Customer.
- Errors.

**Acceptance check:**

- Admin can inspect conversation but cannot reply as company.

---

### T105 — Admin bots — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/bots/page.tsx
frontend-next/src/components/admin/AdminBotsTable.tsx
```

**Data:**

```txt
GET /admin/bot-integrations
```

**Table columns:**

- company.
- bot username.
- linked project.
- status.
- readiness.
- last error.
- messages today.

**Acceptance check:**

- Read-only list works for `platform_owner`.

---

### T106 — Admin errors — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/errors/page.tsx
frontend-next/src/components/admin/AdminErrorsFeed.tsx
```

**Important:**

There may be no unified `GET /admin/errors` endpoint.

Implement fallback aggregation:

1. Use `GET /security/events` only if platform owner has access and endpoint exists.
2. Use admin bots `last_error`.
3. Use failed document statuses if available from admin/company project detail.
4. Otherwise show honest empty state:

```txt
Unified admin error feed endpoint is not available yet.
```

**Do not create fake errors.**

**Optional backend follow-up task:**

Create `GET /admin/errors` later if product requires unified feed.

**Acceptance check:**

- Page is useful even without unified endpoint.
- No fake data.

---

### T107 — Admin stats — done

**Create:**

```txt
frontend-next/src/app/(admin)/admin/stats/page.tsx
```

**Data:**

```txt
GET /admin/stats
GET /admin/overview
```

**Show:**

- company growth if available.
- messages count.
- conversations count.
- documents count.
- bot usage.
- top active companies.
- failed answers if available.

If advanced chart data is unavailable, show metric cards and “not available yet” placeholders.

**Acceptance check:**

- Page is honest about missing advanced stats.

---

## Phase 11 — Utilities and Polishing

### T110 — Formatters and status helpers — done

**Create:**

```txt
frontend-next/src/lib/utils/formatters.ts
frontend-next/src/lib/utils/dates.ts
frontend-next/src/lib/utils/status.ts
```

**Implement:**

- date/time format.
- number format.
- status to badge variant.
- role label.
- document status label.
- bot readiness label.
- conversation status label.

**Acceptance check:**

- No page manually formats statuses inconsistently.

---

### T111 — Responsive behavior

**Do:**

- Sidebar collapses on mobile.
- Tables are scrollable on small screens.
- Conversation inbox becomes stacked on mobile.
- Forms fit mobile width.
- Dialogs/sheets are usable on mobile.

**Acceptance check:**

- Manually test widths: 375px, 768px, 1280px.

---

### T112 — Arabic/English friendly UI

**Do:**

- Avoid hardcoded layout assumptions that break RTL.
- Use clear English labels for v1, but structure should support Arabic later.
- Keep text centralized where practical.

**Acceptance check:**

- Long Arabic bot/project names do not break cards/tables.

---

### T113 — Query invalidation — done

**Do:**

Use TanStack Query invalidations:

- After create/update/delete project -> invalidate `projects`.
- After upload/process/delete document -> invalidate `documents`, `projectStats`, `tasks`.
- After bot create/update/delete/enable/disable/rotate -> invalidate `botIntegrations`, `botReadiness`.
- After conversation actions -> invalidate `conversations`, `conversation`, `messages`.
- After admin company action -> invalidate `adminCompanies`, `adminCompany`.

**Acceptance check:**

- UI updates after mutations without hard refresh.

---

### T114 — Error boundaries and not found — done

**Create:**

```txt
frontend-next/src/app/not-found.tsx
frontend-next/src/app/error.tsx
```

**Acceptance check:**

- Unknown route shows professional page.
- Unhandled render error shows professional fallback.

---

## Phase 12 — Verification

### T120 — Typecheck and build — done

**Run:**

```bash
cd frontend-next
pnpm typecheck
pnpm build
```

**Acceptance check:**

- Both pass.

---

### T121 — Manual smoke test

With backend running on `http://localhost:8000` and Next running on `http://localhost:3001`, verify:

1. `/login` shows backend health.
2. Login works.
3. `company_admin` redirects to `/dashboard`.
4. `platform_owner` redirects to `/admin`.
5. `company_admin` cannot see Admin Console link.
6. Direct `/admin` as `company_admin` shows forbidden/redirect.
7. `/knowledge-bases` lists projects.
8. Create knowledge base works.
9. Upload document works.
10. Process/index document starts task.
11. Task status polls.
12. Test Chat calls `/projects/{id}/query`.
13. `/telegram-bots` lists bot integrations.
14. Create bot flow does not display saved token after save.
15. Rotate token flow only displays input before submission.
16. `/conversations` lists conversations.
17. Conversation detail loads messages.
18. Manual reply works.
19. Resolve/escalate/assign/block actions work.
20. `/admin/companies` works for platform owner.
21. `/admin/conversations/{id}` is read-only.
22. `/admin/bots` works.
23. `/admin/errors` does not fake missing endpoint.
24. `/ai-settings` does not allow company admin to mutate global config.
25. No page uses `/bot/config`.
26. No page uses `active_project_id`.

---

### T122 — Search-based regression checks — done

Run from repo root:

```bash
rg -n "bot/config|active_project_id|prompt\\(|confirm\\(|document\\.getElementById|querySelector" frontend-next
```

**Expected:**

- No `/bot/config`.
- No `active_project_id`.
- No `prompt(`.
- No browser `confirm(`.
- No direct DOM manipulation.

Allow `querySelector` only if created by generated library code, not app code.

---

### T123 — README update — done

**Modify:**

```txt
README.md
AGENTS.md
```

**README add:**

- New frontend path: `frontend-next/`.
- Dev command: `cd frontend-next && pnpm dev`.
- URL: `http://localhost:3001`.
- Required env: `NEXT_PUBLIC_API_BASE_URL`.
- Old `frontend/` remains during migration.

**AGENTS.md add compact note:**

- New Next.js frontend exists in `frontend-next/`.
- Do not use legacy `/bot/config` in new frontend.
- New frontend API modules live under `frontend-next/src/lib/api/`.
- Auth uses Bearer token compatibility for this round.

**Acceptance check:**

- Docs remain concise.
- AGENTS.md does not become huge.

---

## Phase 13 — Optional Backend Gap Tasks

Only do these if explicitly approved. Do not silently add backend scope while building frontend.

### BT001 — Account profile update endpoint

Need only if product requires editing company name/website.

Possible endpoint:

```txt
PATCH /account/profile
```

Frontend currently should show profile fields read-only unless endpoint exists.

---

### BT002 — Unified admin errors endpoint

Need only if `/admin/errors` must be real backend data.

Possible endpoint:

```txt
GET /admin/errors
```

Should aggregate:

- webhook errors.
- token validation errors.
- LLM errors.
- document processing errors.
- security events.

---

### BT003 — Per-company AI settings

Need only if company admins should mutate AI settings.

Current `/config/providers` appears global/runtime-level. Do not let company admins mutate it unless backend becomes tenant-scoped.

---

### BT004 — Extra bot settings fields

Need only if backend model does not support:

- language.
- tone.
- welcome message.
- handoff message.
- collect contact enabled.

Do not send unsupported fields.

---

# Final Acceptance Criteria

The migration is successful when:

1. New frontend lives in `frontend-next/`.
2. Old `frontend/` still exists.
3. Login/signup work with existing backend.
4. `company_admin` reaches `/dashboard`.
5. `platform_owner` reaches `/admin`.
6. `company_admin` cannot see Admin Console.
7. `company_admin` cannot directly access `/admin/*`.
8. Knowledge bases show backend projects.
9. Documents upload/process/query flow works.
10. Smart Chat uses `POST /projects/{id}/query`.
11. Telegram bots use `/bot-integrations`.
12. Saved Telegram token is never displayed.
13. Conversations use `/conversations`.
14. Conversation detail shows messages/sources internally when available.
15. Manual reply/resolve/escalate/assign/block work for company workspace.
16. Admin Console uses `/admin/*`.
17. Admin conversation detail is read-only.
18. Frontend does not use `/bot/config`.
19. Frontend does not use `active_project_id`.
20. Every page has loading/empty/error states.
21. UI is responsive.
22. UI looks like a professional SaaS product, not a demo.
23. `pnpm typecheck` passes.
24. `pnpm build` passes.
