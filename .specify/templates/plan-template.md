# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The plan MUST answer each RAGMind constitutional gate before implementation:

- **RAG core preservation**: Identify any touched upload, processing, chunking,
  embedding, vector retrieval, or answer-generation paths. Confirm
  `POST /projects/{project_id}/query` remains available when relevant.
- **Tenant isolation**: Show how `owner_id == current_user.id` is enforced for
  company flows and how retrieval preserves `owner_id` and `project_id` scope.
- **Platform-owner access**: Confirm cross-company behavior, if any, is limited
  to `platform_owner` users through `/admin/*` routes and Admin Console views.
- **Role separation**: Confirm dashboard users and Telegram customers remain
  separate concepts and that Telegram customers do not authenticate as users.
- **Bot integration source of truth**: Confirm production Telegram behavior
  resolves through database-backed bot integrations, not global bot config,
  service-account login, project auto-selection, or one global bot.
- **Secret protection**: Document token encryption, hashing, redaction,
  response filtering, logging constraints, and rotation behavior when bot tokens
  or webhook secrets are touched.
- **Durable conversations**: Confirm Telegram customer profiles, conversations,
  customer messages, bot replies, agent/system/error messages, sources, and
  retrieval metadata are stored when customer-support flows are touched.
- **Customer-safe answers**: Confirm customer replies hide internal sources and
  retrieval/debug data by default and expose sources only by explicit setting.
- **Human handoff**: Confirm support workflows preserve manual reply,
  escalation, resolution, block, assignment, or explicit future extension points.
- **Backend enforcement**: Confirm role, ownership, account status,
  bot/project, conversation, source visibility, and no-auto-switch rules are
  enforced server-side.
- **Minimal compatibility**: Explain why the design extends existing routes,
  controllers, services, and models without unnecessary rewrites.
- **Operational readiness**: Define readiness/status checks and fail-safe
  behavior for affected integrations.
- **Verification**: List tests or smoke checks for RAG compatibility, tenant
  isolation, admin access, bot linking, webhook behavior, source hiding, no
  service/admin login, and no project auto-switching as applicable.
- **Documentation**: List required updates to `AGENTS.md`,
  `backend/ENDPOINTS.md`, `README.md`, and `docs/project-graph.md` when
  structural, setup, endpoint, or architecture behavior changes.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
