# API Binding Inventory

This inventory tracks frontend routes against real backend API clients. It is a guard against visually correct but unbound UI.

## Auth Routes

| Route | Frontend files | API bindings | Backend routes |
|---|---|---|---|
| `/login` | `frontend-next/src/app/(auth)/login/page.tsx` | `login`, `getMe`, `getHealth` | `POST /auth/login`, `GET /auth/me`, `GET /health` |
| `/signup` | `frontend-next/src/app/(auth)/signup/page.tsx` | `signup` | `POST /auth/signup` |

## Company Routes

| Route | Frontend files | API bindings | Backend routes |
|---|---|---|---|
| `/dashboard` | `frontend-next/src/app/(company)/dashboard/page.tsx`, `frontend-next/src/components/dashboard/` | `listProjects`, `listBotIntegrations`, `listConversations` | `GET /projects/`, `GET /bot-integrations/`, `GET /conversations/` |
| `/onboarding` | `frontend-next/src/app/(company)/onboarding/page.tsx` | Product route links only | Existing company routes |
| `/knowledge-bases` | `frontend-next/src/app/(company)/knowledge-bases/page.tsx`, `frontend-next/src/components/knowledge-bases/` | `listProjects`, `createProject` | `GET /projects/`, `POST /projects/` |
| `/knowledge-bases/[projectId]` | `frontend-next/src/app/(company)/knowledge-bases/[projectId]/page.tsx`, `frontend-next/src/components/knowledge-bases/` | `getProject`, `getProjectStats`, `listDocuments`, `uploadDocument`, `processDocument`, `processAndIndexDocument`, `deleteDocument`, `reindexProject`, `askProject`, `listBotIntegrations` | `GET /projects/{id}`, `GET /projects/{id}/stats`, `GET/POST /projects/{id}/documents`, `POST /documents/{id}/process`, `POST /documents/{id}/process-and-index`, `DELETE /documents/{id}`, `POST /projects/{id}/index`, `POST /projects/{id}/query`, `GET /bot-integrations/` |
| `/telegram-bots` | `frontend-next/src/app/(company)/telegram-bots/page.tsx`, `frontend-next/src/components/bots/` | `listBotIntegrations`, `createBotIntegration`, `enableBotIntegration`, `disableBotIntegration`, `listProjects` | `GET/POST /bot-integrations/`, `POST /bot-integrations/{id}/enable`, `POST /bot-integrations/{id}/disable`, `GET /projects/` |
| `/telegram-bots/[botId]` | `frontend-next/src/app/(company)/telegram-bots/[botId]/page.tsx`, `frontend-next/src/components/bots/` | `getBotIntegration`, `getBotReadiness`, `updateBotIntegration`, `rotateBotToken`, `deleteBotIntegration`, `listProjects`, `listConversations` | `GET/PATCH /bot-integrations/{id}`, `GET /bot-integrations/{id}/readiness`, `POST /bot-integrations/{id}/rotate-token`, `DELETE /bot-integrations/{id}`, `GET /projects/`, `GET /conversations/` |
| `/conversations` | `frontend-next/src/app/(company)/conversations/page.tsx`, `frontend-next/src/components/conversations/` | `listConversations` | `GET /conversations/` |
| `/conversations/[conversationId]` | `frontend-next/src/app/(company)/conversations/[conversationId]/page.tsx`, `frontend-next/src/components/conversations/` | `getConversation`, `getConversationMessages`, `replyToConversation`, `resolveConversation`, `escalateConversation`, `assignConversation`, `blockCustomer` | `GET /conversations/{id}`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/reply`, `POST /conversations/{id}/resolve`, `POST /conversations/{id}/escalate`, `POST /conversations/{id}/assign`, `POST /conversations/{id}/block-customer` |
| `/smart-chat` | `frontend-next/src/app/(company)/smart-chat/page.tsx` | `listProjects`, `askProject` | `GET /projects/`, `POST /projects/{id}/query` |
| `/ai-settings` | `frontend-next/src/app/(company)/ai-settings/page.tsx` | `getProviders`, `updateProviders` | `GET /config/providers`, `POST /config/providers` |
| `/account` | `frontend-next/src/app/(company)/account/page.tsx` | `getMe`, `changePassword` | `GET /auth/me`, `POST /auth/change-password` |

## Platform Owner Routes

| Route | Frontend files | API bindings | Backend routes |
|---|---|---|---|
| `/admin` | `frontend-next/src/app/(admin)/admin/page.tsx`, `frontend-next/src/components/admin/` | `getAdminOverview`, `listAdminCompanies`, `listAdminBotIntegrations`, `listAdminConversations` | `GET /admin/overview`, `GET /admin/companies`, `GET /admin/bot-integrations`, `GET /admin/conversations` |
| `/admin/stats` | `frontend-next/src/app/(admin)/admin/stats/page.tsx` | `getAdminStats`, `getAdminOverview` | `GET /admin/stats`, `GET /admin/overview` |
| `/admin/observability` | `frontend-next/src/app/(admin)/admin/observability/page.tsx`, `frontend-next/src/components/admin/AdminObservabilityPanel.tsx` | `getAdminObservabilityDashboards`, `getAdminObservabilitySummary` | `GET /admin/observability/dashboards`, `GET /admin/observability/summary` |
| `/admin/companies` | `frontend-next/src/app/(admin)/admin/companies/page.tsx`, `frontend-next/src/components/admin/CompaniesTable.tsx` | `listAdminCompanies`, `activateCompany`, `suspendCompany`, `blockCompany` | `GET /admin/companies`, `POST /admin/companies/{id}/activate`, `POST /admin/companies/{id}/suspend`, `POST /admin/companies/{id}/block` |
| `/admin/companies/[companyId]` | `frontend-next/src/app/(admin)/admin/companies/[companyId]/page.tsx`, `frontend-next/src/components/admin/CompanyDetailTabs.tsx` | `getAdminCompany`, `listAdminCompanyProjects`, `listAdminCompanyBotIntegrations`, `listAdminCompanyConversations` | `GET /admin/companies/{id}`, `GET /admin/companies/{id}/projects`, `GET /admin/companies/{id}/bot-integrations`, `GET /admin/companies/{id}/conversations` |
| `/admin/bots` | `frontend-next/src/app/(admin)/admin/bots/page.tsx`, `frontend-next/src/components/admin/AdminBotsTable.tsx` | `listAdminBotIntegrations` | `GET /admin/bot-integrations` |
| `/admin/conversations` | `frontend-next/src/app/(admin)/admin/conversations/page.tsx`, `frontend-next/src/components/admin/AdminConversationsTable.tsx` | `listAdminConversations` | `GET /admin/conversations` |
| `/admin/conversations/[conversationId]` | `frontend-next/src/app/(admin)/admin/conversations/[conversationId]/page.tsx` | `getAdminConversation`, `getAdminConversationMessages` | `GET /admin/conversations/{id}`, `GET /admin/conversations/{id}/messages` |
| `/admin/errors` | `frontend-next/src/app/(admin)/admin/errors/page.tsx`, `frontend-next/src/components/admin/AdminErrorsFeed.tsx` | `listAdminBotIntegrations` fallback only | `GET /admin/bot-integrations` |

## Binding Rules

- Do not add dashboard cards with invented counts when an API binding exists.
- If a backend endpoint is unavailable, render an unavailable or empty state and record it in `implementation-notes.md`.
- Add every new API function to this file when it is introduced.
