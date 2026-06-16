# Research: Incremental UI/UX Upgrade

## Decision 1: Keep `frontend-next` As The Production App

**Decision**: Upgrade the existing `frontend-next` codebase in-place, block by block. Do not replace it with a generated new app. A `new front` folder can exist only as an optional visual prototype/staging reference if explicitly needed later.

**Rationale**: The current app already contains route groups, API clients, auth hydration, role guards, and domain components for company and platform-owner workflows. Replacing it would risk dropping existing behavior and directly conflicts with the feature requirement to avoid deleting long code and generating a new frontend.

**Alternatives considered**:

- Build a full new app in `new front`: rejected because it creates duplicate runtime ownership and high integration risk.
- Recreate pages from screenshots only: rejected because it would ignore current backend contracts and role rules.

## Decision 2: Use The Screenshot Style As A System, Not A Pixel Copy

**Decision**: Match the references in `screens/*.png` through a reusable product dashboard language: dark sidebar, light workspace, compact topbar, dense metric cards, table-first content, right-side drawers, badge/status language, progress bars, chart cards, and concise admin panels.

**Rationale**: The screenshots describe a coherent SaaS operations interface. The repo needs maintainable reusable components rather than one-off copied screens.

**Alternatives considered**:

- Pixel-perfect clone: rejected because current data and states differ from the mock images.
- Generic shadcn defaults: rejected because the user specifically requested the screenshot dashboard direction.

## Decision 3: Add Missing Requested UI Dependencies Deliberately

**Decision**: Keep existing installed stack and add the requested missing packages: `@tanstack/react-table` and `recharts`. Review patch upgrades for already installed packages rather than bumping everything blindly.

**Rationale**: `frontend-next/package.json` already includes Next.js, TypeScript, Tailwind CSS, shadcn, TanStack Query, React Hook Form, Zod, Zustand, and Lucide. It does not currently include TanStack Table or Recharts. Current package checks on 2026-06-13 showed newer patch/minor versions are available for several packages, but the plan should separate dependency addition from broad upgrades to reduce regression risk.

**Alternatives considered**:

- Use the current simple `DataTable` only: rejected because the user explicitly requested TanStack Table and the app needs sorting/filtering/pagination patterns.
- Replace all package versions immediately: rejected because visual work and dependency upgrades should be validated separately.

## Decision 4: Use shadcn Components Before Custom Markup

**Decision**: Use existing shadcn UI components first, then add missing components through `pnpm dlx shadcn@latest add` after checking docs. Candidate additions: `sidebar`, `chart`, `field`, `input-group`, `empty`, `progress`, `tooltip`, `checkbox`, `switch`, `pagination`, `drawer`, and `command`.

**Rationale**: The project is configured as shadcn radix-nova, RSC-enabled, Tailwind v4, and Lucide-based. The shadcn docs command confirmed official component docs/examples for those components.

**Alternatives considered**:

- Hand-build sidebars, forms, empty states, and chart containers: rejected because it duplicates shadcn patterns and increases accessibility risk.
- Force-overwrite existing components from the registry: rejected because local components may already be customized and must be merged carefully.

## Decision 5: Standardize Data Fetching Around TanStack Query

**Decision**: Keep `apiRequest` and TanStack Query as the primary frontend/backend integration layer. Introduce stable query key factories and shared mutation invalidation patterns as part of the UI upgrade.

**Rationale**: The app already uses TanStack Query across company and admin pages. Centralized keys will reduce accidental stale data while preserving the current Bearer-token API client.

**Alternatives considered**:

- Move all fetching to server components: rejected for this round because auth state is currently client-hydrated and existing pages are client components.
- Use ad hoc fetch calls per page: rejected because it weakens cache consistency.

## Decision 6: Use TanStack Table For Operational Tables

**Decision**: Evolve the shared table layer to use TanStack Table for companies, bots, conversations, knowledge bases, documents, and readiness/error tables.

**Rationale**: Current tables are mostly static wrappers. The screenshot references show sortable, filterable, action-heavy operations tables. TanStack Table supports this without changing backend behavior.

**Alternatives considered**:

- Add sorting/filtering manually to each table: rejected because it would duplicate logic and create inconsistent behavior.

## Decision 7: Use React Hook Form And Zod For Forms

**Decision**: Normalize create/edit flows around React Hook Form plus Zod schemas, especially bot creation/rotation, knowledge-base forms, account/password changes, AI settings, and filters.

**Rationale**: These libraries are already requested and partially installed. They improve validation clarity while preserving existing backend payloads.

**Alternatives considered**:

- Keep local uncontrolled forms: rejected where validation and error presentation are important.
- Move validation only to backend: rejected because users need immediate form feedback.

## Decision 8: Backend-Mediated Observability Integration

**Decision**: Add platform-owner-only backend routes that expose a curated dashboard catalog, health/target summary, and optional metric summaries. The frontend should not hold Grafana credentials or send arbitrary PromQL directly to Prometheus.

**Rationale**: Compose already provisions Grafana, Prometheus, node-exporter, postgres-exporter, backend metrics, and Celery metrics. The product owner needs a page to switch between these dashboards, but raw infrastructure ports and default credentials must not become frontend assumptions.

**Alternatives considered**:

- Direct iframe to `http://127.0.0.1:3000`: rejected as the only integration because it depends on browser-local ports, Grafana embedding/auth settings, and leaks environment assumptions.
- Direct Prometheus browser queries: rejected because Prometheus should remain infrastructure-facing.

## Decision 9: Preserve Role Boundaries And Current Backend Logic

**Decision**: Company pages continue to use company-scoped APIs; platform-owner pages continue to use `/admin/*` APIs; observability is added under the same platform-owner boundary.

**Rationale**: Code-review-graph flags backend route/security/service coupling as a high-risk integration area. Keeping the existing auth dependencies and adding narrow routes reduces blast radius.

**Alternatives considered**:

- Let all authenticated users view observability: rejected because system-wide metrics are platform-owner concerns.

## Decision 10: Test Per Block, Then End-To-End

**Decision**: Each block upgrade must include local validation notes, then the feature closes with lint, typecheck, build, targeted backend tests, and browser checks across desktop and mobile viewports.

**Rationale**: The user explicitly requested careful testing and verification. Block-level validation prevents a broad visual rewrite from hiding regressions.

**Alternatives considered**:

- Test only after all pages are complete: rejected because failures would be harder to isolate.
