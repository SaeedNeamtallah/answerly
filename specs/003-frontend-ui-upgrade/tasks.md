# Tasks: Incremental UI/UX Upgrade

**Input**: Design documents from `specs/003-frontend-ui-upgrade/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Tests**: Required for this feature because the user explicitly requested testing and verified frontend-to-backend logic.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks.
- **[Story]**: Maps to the user stories in `spec.md`.
- Every task includes exact paths and must preserve real backend bindings. No fake/static dashboard logic is acceptable unless it is an explicit unavailable-state fallback.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare dependencies, references, and baseline inventories before UI changes.

- [X] T001 Create implementation notes file for block-by-block progress in `specs/003-frontend-ui-upgrade/implementation-notes.md`
- [X] T002 Update frontend dependencies for TanStack Table, Recharts, and frontend test tooling in `frontend-next/package.json` and `frontend-next/pnpm-lock.yaml`
- [X] T003 Add missing shadcn/ui components with CLI-reviewed diffs in `frontend-next/src/components/ui/`
- [X] T004 [P] Document screenshot-derived dashboard patterns from `screens/*.png` in `specs/003-frontend-ui-upgrade/design-reference.md`
- [X] T005 [P] Create route-to-backend API binding inventory for all current pages in `specs/003-frontend-ui-upgrade/api-binding-inventory.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared code that all page/block upgrades depend on.

**Critical**: No user story page work should begin until this phase is complete.

- [X] T006 Create centralized TanStack Query key factories in `frontend-next/src/lib/api/queryKeys.ts`
- [X] T007 Harden shared API error handling and typed unavailable-state behavior in `frontend-next/src/lib/api/client.ts`
- [X] T008 Evolve the shared table layer to TanStack Table in `frontend-next/src/components/shared/DataTable.tsx`
- [X] T009 [P] Add table toolbar and pagination helpers in `frontend-next/src/components/shared/DataTableToolbar.tsx` and `frontend-next/src/components/shared/DataTablePagination.tsx`
- [X] T010 [P] Upgrade shared metric/status/empty/loading/error blocks in `frontend-next/src/components/shared/MetricCard.tsx`, `frontend-next/src/components/shared/StatusBadge.tsx`, `frontend-next/src/components/shared/EmptyState.tsx`, `frontend-next/src/components/shared/LoadingState.tsx`, and `frontend-next/src/components/shared/ErrorState.tsx`
- [X] T011 Add shared form schema and field helpers for React Hook Form and Zod in `frontend-next/src/lib/validation/` and `frontend-next/src/components/shared/FormSection.tsx`
- [X] T012 Upgrade global visual tokens and layout primitives in `frontend-next/src/app/globals.css`, `frontend-next/src/components/layout/AppShell.tsx`, `frontend-next/src/components/layout/Sidebar.tsx`, `frontend-next/src/components/layout/Topbar.tsx`, and `frontend-next/src/components/layout/MobileNav.tsx`
- [X] T013 Create block registry and validation evidence structure in `specs/003-frontend-ui-upgrade/block-map.md` and `specs/003-frontend-ui-upgrade/validation-evidence.md`
- [X] T014 [P] Create a frontend backend-binding audit script that flags route-level fake data and missing API mappings in `tools/frontend_backend_binding_audit.py`
- [X] T015 Add Playwright configuration and reusable authenticated test helpers in `frontend-next/playwright.config.ts` and `frontend-next/tests/e2e/helpers/auth.ts`

**Checkpoint**: Shared design, data fetching, table, validation, and test foundations are ready.

---

## Phase 3: User Story 1 - Improve Existing Blocks Without Workflow Disruption (Priority: P1) MVP

**Goal**: Upgrade existing product blocks to the reference dashboard quality while preserving workflows, auth, permissions, backend payloads, and real API-driven data.

**Independent Test**: Select one upgraded block, verify the route still loads for the intended role, verify its primary action still calls the real backend API through `frontend-next/src/lib/api/`, and verify the block is clearer without losing fields/actions/status information.

### Tests for User Story 1

- [X] T016 [P] [US1] Add platform-owner observability backend route tests in `backend/tests/test_admin_observability.py`
- [ ] T017 [P] [US1] Add backend-bound company journey browser tests in `frontend-next/tests/e2e/company-backend-bound.spec.ts`
- [ ] T018 [P] [US1] Add platform-owner observability browser tests in `frontend-next/tests/e2e/admin-observability.spec.ts`

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement platform-owner observability service with curated Grafana and Prometheus access in `backend/services/observability_service.py`
- [X] T020 [US1] Add platform-owner observability routes and register them in `backend/routes/admin_observability.py`, `backend/routes/__init__.py`, and `backend/main.py`
- [X] T021 [P] [US1] Add observability TypeScript response types in `frontend-next/src/lib/types/admin.ts`
- [X] T022 [US1] Add real admin observability API client functions in `frontend-next/src/lib/api/admin.ts`
- [X] T023 [US1] Add the Observability admin navigation item without removing existing admin routes in `frontend-next/src/components/layout/Sidebar.tsx` and `frontend-next/src/components/layout/Topbar.tsx`
- [X] T024 [US1] Create the backend-bound platform-owner Observability page in `frontend-next/src/app/(admin)/admin/observability/page.tsx` and `frontend-next/src/components/admin/AdminObservabilityPanel.tsx`
- [X] T025 [US1] Upgrade the authenticated app shell to the screenshot-style sidebar/topbar while preserving role guards in `frontend-next/src/components/layout/AppShell.tsx`, `frontend-next/src/components/layout/RoleGuard.tsx`, `frontend-next/src/components/layout/Sidebar.tsx`, and `frontend-next/src/components/layout/Topbar.tsx`
- [ ] T026 [P] [US1] Upgrade login and signup UI while preserving `/auth/login`, `/auth/signup`, `/auth/me`, and `/health` calls in `frontend-next/src/app/(auth)/login/page.tsx`, `frontend-next/src/app/(auth)/signup/page.tsx`, `frontend-next/src/lib/api/auth.ts`, and `frontend-next/src/lib/api/health.ts`
- [X] T027 [US1] Upgrade the company dashboard using only real `listProjects`, `listBotIntegrations`, and `listConversations` data in `frontend-next/src/app/(company)/dashboard/page.tsx` and `frontend-next/src/components/dashboard/`
- [ ] T028 [US1] Upgrade onboarding blocks while preserving navigation to real product routes in `frontend-next/src/app/(company)/onboarding/page.tsx`
- [ ] T029 [US1] Upgrade knowledge-base list and detail pages while preserving project/document API calls in `frontend-next/src/app/(company)/knowledge-bases/page.tsx`, `frontend-next/src/app/(company)/knowledge-bases/[projectId]/page.tsx`, `frontend-next/src/lib/api/projects.ts`, and `frontend-next/src/lib/api/documents.ts`
- [ ] T030 [US1] Upgrade knowledge-base cards, tables, upload, linked bot, and test chat blocks without dropping existing actions in `frontend-next/src/components/knowledge-bases/`
- [ ] T031 [US1] Upgrade Telegram bot list and detail pages while preserving create, update, enable, disable, rotate-token, readiness, and delete API flows in `frontend-next/src/app/(company)/telegram-bots/page.tsx`, `frontend-next/src/app/(company)/telegram-bots/[botId]/page.tsx`, and `frontend-next/src/lib/api/botIntegrations.ts`
- [ ] T032 [US1] Upgrade bot card, table, readiness, form drawer, and token rotation blocks while keeping submitted payloads backend-compatible in `frontend-next/src/components/bots/`
- [ ] T033 [US1] Upgrade conversation list and detail pages while preserving list, messages, reply, resolve, escalate, assign, and block-customer API flows in `frontend-next/src/app/(company)/conversations/page.tsx`, `frontend-next/src/app/(company)/conversations/[conversationId]/page.tsx`, and `frontend-next/src/lib/api/conversations.ts`
- [ ] T034 [US1] Upgrade conversation thread, filters, metadata, source panel, and reply composer blocks without exposing internal sources unless existing flags allow it in `frontend-next/src/components/conversations/`
- [ ] T035 [US1] Upgrade smart chat while preserving real project query submission through `/projects/{project_id}/query` in `frontend-next/src/app/(company)/smart-chat/page.tsx` and `frontend-next/src/lib/api/query.ts`
- [ ] T036 [US1] Upgrade AI settings and account pages while preserving provider config and password-change backend calls in `frontend-next/src/app/(company)/ai-settings/page.tsx`, `frontend-next/src/app/(company)/account/page.tsx`, `frontend-next/src/lib/api/config.ts`, and `frontend-next/src/lib/api/auth.ts`
- [ ] T037 [US1] Upgrade admin overview and stats pages while preserving `/admin/overview` and `/admin/stats` bindings in `frontend-next/src/app/(admin)/admin/page.tsx`, `frontend-next/src/app/(admin)/admin/stats/page.tsx`, and `frontend-next/src/components/admin/AdminMetricCards.tsx`
- [ ] T038 [US1] Upgrade admin companies and company detail pages while preserving activate, suspend, block, company projects, company bots, and company conversations API flows in `frontend-next/src/app/(admin)/admin/companies/page.tsx`, `frontend-next/src/app/(admin)/admin/companies/[companyId]/page.tsx`, and `frontend-next/src/components/admin/CompaniesTable.tsx`
- [ ] T039 [US1] Upgrade admin bots, admin conversations, admin conversation detail, and admin errors pages while preserving real `/admin/*` API bindings in `frontend-next/src/app/(admin)/admin/bots/page.tsx`, `frontend-next/src/app/(admin)/admin/conversations/page.tsx`, `frontend-next/src/app/(admin)/admin/conversations/[conversationId]/page.tsx`, `frontend-next/src/app/(admin)/admin/errors/page.tsx`, and `frontend-next/src/components/admin/`
- [X] T040 [US1] Remove or justify any static placeholder operational data found by the binding audit in `frontend-next/src/app/`, `frontend-next/src/components/`, and `specs/003-frontend-ui-upgrade/api-binding-inventory.md`
- [X] T041 [US1] Record US1 backend-binding validation results in `specs/003-frontend-ui-upgrade/validation-evidence.md`

**Checkpoint**: Existing product workflows are visually upgraded and still backed by real backend calls.

---

## Phase 4: User Story 2 - Review Upgrades Block By Block (Priority: P2)

**Goal**: Make each UI upgrade reviewable as a bounded block with preserved behavior, explicit backend dependencies, and validation evidence before moving to the next unrelated block.

**Independent Test**: Review one completed block in `block-map.md` and confirm it lists the route, components, API clients, query keys, preserved actions, changed files, and validation evidence.

### Tests for User Story 2

- [ ] T042 [P] [US2] Add a binding-audit invocation to the smoke workflow in `tools/test_all.py`
- [ ] T043 [P] [US2] Add documentation consistency checks for block map and validation evidence in `tools/frontend_backend_binding_audit.py`

### Implementation for User Story 2

- [ ] T044 [US2] Populate every upgraded page surface and component block in `specs/003-frontend-ui-upgrade/block-map.md`
- [ ] T045 [US2] Update API dependencies, query keys, and mutation invalidation notes for each upgraded block in `specs/003-frontend-ui-upgrade/api-binding-inventory.md`
- [ ] T046 [US2] Add block-level validation notes for each completed page surface in `specs/003-frontend-ui-upgrade/validation-evidence.md`
- [ ] T047 [US2] Add review checklist guidance for backend-bound UI blocks in `specs/003-frontend-ui-upgrade/review-checklist.md`
- [ ] T048 [US2] Ensure implementation notes identify every intentionally changed behavior and every preserved behavior in `specs/003-frontend-ui-upgrade/implementation-notes.md`
- [ ] T049 [US2] Run the binding audit and resolve all fake-data or missing-API findings in `tools/frontend_backend_binding_audit.py` and `frontend-next/src/`

**Checkpoint**: Every upgraded block has traceable review evidence and no unbound frontend behavior is hidden.

---

## Phase 5: User Story 3 - Maintain Responsive And Accessible Use (Priority: P3)

**Goal**: Ensure upgraded blocks remain readable, navigable, and usable across viewport sizes and input methods.

**Independent Test**: Run responsive and keyboard browser checks for at least one upgraded company page and one platform-owner page, confirming no overlapping content, clipped primary text, hidden actions, or broken focus flow.

### Tests for User Story 3

- [ ] T050 [P] [US3] Add responsive viewport browser tests for company and admin routes in `frontend-next/tests/e2e/responsive-layout.spec.ts`
- [ ] T051 [P] [US3] Add keyboard navigation and focus visibility browser tests in `frontend-next/tests/e2e/keyboard-accessibility.spec.ts`

### Implementation for User Story 3

- [ ] T052 [US3] Improve mobile and tablet navigation behavior in `frontend-next/src/components/layout/MobileNav.tsx`, `frontend-next/src/components/layout/Sidebar.tsx`, and `frontend-next/src/components/layout/Topbar.tsx`
- [ ] T053 [US3] Add stable overflow, truncation, and responsive density behavior to shared tables and cards in `frontend-next/src/components/shared/DataTable.tsx`, `frontend-next/src/components/shared/DataTableToolbar.tsx`, `frontend-next/src/components/shared/DataTablePagination.tsx`, and `frontend-next/src/components/shared/MetricCard.tsx`
- [ ] T054 [US3] Add accessible labels, dialog titles, drawer titles, focus states, and disabled states across bot and knowledge-base controls in `frontend-next/src/components/bots/` and `frontend-next/src/components/knowledge-bases/`
- [ ] T055 [US3] Add responsive chart and observability fallback behavior in `frontend-next/src/components/admin/AdminObservabilityPanel.tsx` and `frontend-next/src/components/dashboard/`
- [ ] T056 [US3] Fix mobile layout issues in auth, company, and admin route pages under `frontend-next/src/app/`
- [ ] T057 [US3] Capture desktop, tablet, and mobile validation evidence in `specs/003-frontend-ui-upgrade/validation-evidence.md`

**Checkpoint**: Upgraded UI is responsive and accessible enough for implementation review.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and repository map updates.

- [ ] T058 [P] Update user-facing setup and frontend notes for the upgraded dashboard and observability page in `README.md`
- [X] T059 Update repository map for new frontend dependencies, observability routes, frontend pages, and validation workflow in `AGENTS.md`
- [X] T060 Run frontend lint, typecheck, and build from `frontend-next/package.json` and record results in `specs/003-frontend-ui-upgrade/validation-evidence.md`
- [X] T061 Run backend observability and admin authorization tests from `backend/tests/test_admin_observability.py`, `backend/tests/test_platform_admin.py`, and `backend/tests/test_admin_service.py`
- [ ] T062 Run browser smoke and responsive tests from `frontend-next/tests/e2e/` and record screenshot or trace paths in `specs/003-frontend-ui-upgrade/validation-evidence.md`
- [ ] T063 Run the frontend backend-binding audit and authenticated smoke workflow from `tools/frontend_backend_binding_audit.py` and `tools/test_all.py`
- [ ] T064 Perform final review for deleted/recreated frontend paths, fake operational data, broken auth guards, and untested backend bindings in `frontend-next/`, `backend/`, `tools/`, and `specs/003-frontend-ui-upgrade/`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies.
- Foundational (Phase 2): depends on Setup and blocks all user-story work.
- US1: depends on Phase 2 and is the MVP.
- US2: depends on at least one completed US1 block, then can run alongside remaining block upgrades.
- US3: depends on Phase 2 and should run after each relevant visual block, with final pass after US1.
- Polish: depends on desired user stories being complete.

### User Story Dependencies

- US1 has no dependency on US2 or US3 and delivers the MVP.
- US2 depends on blocks existing to review, but each review artifact can be updated as blocks complete.
- US3 depends on upgraded blocks existing, but tests and layout helpers can start after Phase 2.

### Backend Binding Rules

- Every frontend route must list its backend API functions in `specs/003-frontend-ui-upgrade/api-binding-inventory.md`.
- Every page using operational metrics must derive them from backend responses, authenticated API clients, or explicitly marked unavailable states.
- Platform-owner observability must use backend routes in `backend/routes/admin_observability.py`, not browser-side Prometheus or Grafana credentials.
- No task is done if it only makes the UI look correct while the backend flow is broken.

## Parallel Opportunities

- T004 and T005 can run while dependencies are being prepared.
- T009, T010, T014, and parts of T015 can run in parallel after T006 and T007 are understood.
- T016, T017, and T018 can be written in parallel before their implementations.
- T019 and T021 can run in parallel; T020 and T022 then wire them together.
- Page block upgrades in T026 through T039 can run in parallel after shared components and query keys are stable, as long as they do not edit the same files.
- T050 and T051 can run in parallel once Playwright setup exists.

## Parallel Example: User Story 1

```text
Task: "T016 Add platform-owner observability backend route tests in backend/tests/test_admin_observability.py"
Task: "T017 Add backend-bound company journey browser tests in frontend-next/tests/e2e/company-backend-bound.spec.ts"
Task: "T018 Add platform-owner observability browser tests in frontend-next/tests/e2e/admin-observability.spec.ts"
Task: "T019 Implement platform-owner observability service in backend/services/observability_service.py"
Task: "T021 Add observability TypeScript response types in frontend-next/src/lib/types/admin.ts"
```

## Parallel Example: User Story 3

```text
Task: "T050 Add responsive viewport browser tests in frontend-next/tests/e2e/responsive-layout.spec.ts"
Task: "T051 Add keyboard navigation and focus visibility browser tests in frontend-next/tests/e2e/keyboard-accessibility.spec.ts"
Task: "T053 Add responsive table/card behavior in frontend-next/src/components/shared/"
Task: "T054 Add accessible labels and dialog/drawer states in frontend-next/src/components/bots/ and frontend-next/src/components/knowledge-bases/"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 through one vertical slice first: shared shell, company dashboard, and one real backend-bound table.
3. Stop and validate lint, typecheck, browser smoke, and API binding for that slice.
4. Continue page-by-page only after the slice proves the pattern.

### Incremental Delivery

1. Upgrade one bounded block.
2. Validate real backend calls and states.
3. Record evidence in `validation-evidence.md`.
4. Move to the next block only after regressions are resolved or explicitly accepted.

### Quality Gate

The feature is not complete until `pnpm lint`, `pnpm typecheck`, `pnpm build`, backend admin tests, Playwright smoke checks, and the backend-binding audit pass or have documented, accepted blockers.
