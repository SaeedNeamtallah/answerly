# UI Block Map

Each block must preserve its listed API bindings before it can be marked done.

| Block id | Route | Components | API bindings | Status |
|---|---|---|---|---|
| shell.app | company/admin layouts | `AppShell`, `Sidebar`, `Topbar`, `MobileNav`, `RoleGuard` | auth store, role helpers | code complete; browser pending |
| auth.login | `/login` | login page, backend banner | `login`, `getMe`, `getHealth` | planned |
| auth.signup | `/signup` | signup page | `signup` | planned |
| company.dashboard.metrics | `/dashboard` | `MetricCard`, dashboard panels | `listProjects`, `listBotIntegrations`, `listConversations` | code complete; browser pending |
| company.dashboard.readiness | `/dashboard` | `SetupChecklist`, `KnowledgeBaseReadiness`, `BotHealthPanel`, `RecentConversations` | `listProjects`, `listBotIntegrations`, `listConversations` | code complete; browser pending |
| company.knowledge.list | `/knowledge-bases` | knowledge-base cards/table/dialog | `listProjects`, `createProject` | planned |
| company.knowledge.detail | `/knowledge-bases/[projectId]` | documents/upload/test chat/linked bots | project, document, bot, query APIs | planned |
| company.bots.list | `/telegram-bots` | bot cards/table/create drawer | bot integration APIs, projects API | planned |
| company.bots.detail | `/telegram-bots/[botId]` | readiness/edit/rotate/delete blocks | bot detail, readiness, rotate, delete APIs | planned |
| company.conversations.list | `/conversations` | filters/list | `listConversations` | planned |
| company.conversations.detail | `/conversations/[conversationId]` | thread/reply/metadata/source blocks | conversation detail, messages, reply, status APIs | planned |
| company.smart-chat | `/smart-chat` | chat/test panel | `listProjects`, `askProject` | planned |
| company.settings | `/ai-settings` | provider form | provider config APIs | planned |
| company.account | `/account` | profile/password form | `getMe`, `changePassword` | planned |
| admin.overview | `/admin` | metric cards/tables/error feed | admin overview, companies, bots, conversations APIs | planned |
| admin.companies | `/admin/companies` | companies table/actions | company list/status mutation APIs | planned |
| admin.company.detail | `/admin/companies/[companyId]` | tabs for projects/bots/conversations | company detail APIs | planned |
| admin.bots | `/admin/bots` | bots table | admin bot integrations API | planned |
| admin.conversations | `/admin/conversations` | conversation table/detail | admin conversation APIs | planned |
| admin.errors | `/admin/errors` | error fallback feed | admin bot integrations fallback API | planned |
| admin.observability | `/admin/observability` | `AdminObservabilityPanel`, Grafana iframe/link fallback, Prometheus target summary | `getAdminObservabilityDashboards`, `getAdminObservabilitySummary` | code complete; browser pending |

## Completion Rule

Move a block to `approved` only after the route loads, its API bindings are still real, responsive checks pass, and the evidence is recorded in `validation-evidence.md`.
