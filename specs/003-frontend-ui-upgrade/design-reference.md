# Design Reference: Dashboard UI/UX Style

Source images live in `screens/`.

## Visual System

- Dark, fixed left navigation with strong active states and product identity.
- Light main workspace with dense operational content and generous but not decorative whitespace.
- Compact topbar with search, notification, and account/company controls.
- First viewport should show real product status: metrics, tables, readiness, health, and recent activity.
- Cards should be operational and compact, not marketing-style page sections.
- Tables are primary work surfaces for knowledge bases, bots, conversations, companies, and errors.
- Right-side drawers are used for creation and multi-step setup flows.
- Status language is visual and consistent: green for ready/healthy, amber for degraded/indexing, red for failed/attention, neutral for offline/unknown.
- Charts should be compact decision aids: donut health summaries, small trend lines, readiness progress, and metric strips.

## Reference Mapping

- `ChatGPT Image Jun 14, 2026, 12_43_42 AM (1).png`: company dashboard shell, metric cards, setup checklist, bot health, recent conversations, readiness table.
- `ChatGPT Image Jun 14, 2026, 12_43_43 AM (4).png`: knowledge-base list, table/card toggle pattern, hero block, search/filter actions, bottom tips row.
- `ChatGPT Image Jun 14, 2026, 12_43_45 AM (7).png`: Telegram bots table, right create drawer, bot status metrics, readiness summary.
- `ChatGPT Image Jun 14, 2026, 12_43_46 AM (10).png`: platform-owner admin overview, admin nav grouping, global metrics, recent companies/errors/conversations, usage summary.

## Implementation Rules

- Use the screenshots as a style system, not fixed content.
- Preserve backend truth and role rules over visual mock content.
- Use real data from `frontend-next/src/lib/api/*`.
- Prefer shadcn components and local shared components before custom markup.
- Keep responsive constraints explicit for cards, tables, charts, and drawers.
