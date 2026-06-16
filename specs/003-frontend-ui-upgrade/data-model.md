# Data Model: Incremental UI/UX Upgrade

This feature is mostly UI and integration work. The entities below describe planning, runtime contracts, and validation evidence. They do not require new persistent user-facing database tables unless implementation chooses to persist observability configuration.

## Entity: UIUpgradeBlock

**Purpose**: A bounded interface area upgraded independently.

**Fields**:

- `id`: Stable block identifier, for example `company-dashboard.metric-strip`.
- `route`: Route or layout surface containing the block.
- `audience`: `company_admin`, `platform_owner`, or `all_authenticated`.
- `current_components`: Existing page/components that must remain represented.
- `target_pattern`: Target UI pattern such as metric card strip, operations table, right drawer, chart panel, or settings form.
- `backend_dependencies`: API functions and query keys used by the block.
- `states_required`: Loading, empty, error, disabled, success, and data states that apply.
- `status`: `planned`, `in_progress`, `ready_for_review`, `approved`, or `blocked`.
- `validation_evidence`: References to screenshots, commands, or notes proving the block is safe.

**Validation Rules**:

- Each block must map to existing components before editing starts.
- Each block must preserve existing primary actions and backend payloads unless a separate task changes them.
- Each block must include responsive and keyboard validation before approval.

## Entity: PageSurface

**Purpose**: A full route-level user surface that contains one or more upgrade blocks.

**Fields**:

- `path`: Route path, for example `/dashboard` or `/admin/stats`.
- `layout_variant`: `company`, `admin`, or `auth`.
- `primary_user_goal`: Main task supported by the page.
- `blocks`: Ordered list of `UIUpgradeBlock` ids.
- `api_contracts`: Current backend APIs required by the page.
- `criticality`: `critical`, `important`, or `supporting`.

**Validation Rules**:

- Critical surfaces include login, dashboard, knowledge bases, Telegram bots, conversations, AI settings, account, admin overview, admin companies, admin conversations, admin bots, and observability.
- No surface is considered complete until all existing components on that surface are accounted for.

## Entity: DesignReference

**Purpose**: A screenshot-derived visual target.

**Fields**:

- `source`: File reference under `screens/`.
- `patterns`: Sidebar, topbar, metric cards, tables, charts, drawers, badges, progress, or command/search.
- `applicability`: Routes or blocks where the pattern applies.
- `notes`: Specific observations such as density, spacing, badge treatment, or drawer behavior.

**Validation Rules**:

- References guide composition and density, not exact static content.
- No reference can override existing product permissions or backend data truth.

## Entity: DashboardCatalogItem

**Purpose**: A platform-owner-visible observability dashboard entry.

**Fields**:

- `uid`: Grafana dashboard uid, for example `ragmind-overview`.
- `title`: Human-readable dashboard title.
- `category`: `application`, `api`, `database`, or `infrastructure`.
- `description`: Short purpose text.
- `source`: `grafana`, `prometheus`, or `backend_health`.
- `open_url`: URL to open the dashboard in Grafana when available.
- `embed_url`: Optional safe embed URL when embedding is configured and allowed.
- `panels`: Optional curated panel metadata.
- `status`: `available`, `unavailable`, or `misconfigured`.

**Validation Rules**:

- Dashboard catalog is platform-owner-only.
- Frontend never stores Grafana credentials.
- Catalog must handle unavailable Grafana/Prometheus gracefully.

## Entity: ObservabilitySummary

**Purpose**: Backend-provided system status for the product-owner observability page.

**Fields**:

- `range`: Time range, for example `1h`, `24h`, or `7d`.
- `health`: Backend health/full-health status fields.
- `targets`: Prometheus scrape target states by job.
- `metrics`: Curated metrics such as request rate, p95 latency, 5xx count, document outcomes, query failures, embedding errors, webhook failures, Celery task duration, database connection indicators, and host resource indicators when available.
- `generated_at`: Timestamp when the backend assembled the response.

**Validation Rules**:

- Only allow curated metrics or whitelisted Prometheus queries.
- Unknown or missing metrics return an explicit unavailable state instead of breaking the page.

## Entity: ValidationEvidence

**Purpose**: Proof that a block upgrade preserved behavior and improved usability.

**Fields**:

- `block_id`: Related `UIUpgradeBlock`.
- `commands_run`: Lint, typecheck, build, tests, or smoke checks.
- `viewport_checks`: Desktop, tablet, and mobile screenshots or notes.
- `interaction_checks`: Keyboard, pointer, form, table, drawer, and navigation checks.
- `api_checks`: Backend calls exercised and results.
- `regressions`: Known issues and disposition.

**Validation Rules**:

- Evidence is required before a block can move to `approved`.
- Known regressions must be fixed or explicitly accepted before another unrelated block is marked ready.

## State Transitions

```text
planned -> in_progress -> ready_for_review -> approved
planned -> in_progress -> blocked
blocked -> in_progress
ready_for_review -> in_progress
```

`approved` requires passing the UI block contract, relevant route smoke checks, and no known critical journey regression.
