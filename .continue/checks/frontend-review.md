---
name: Frontend Review
description: Review frontend/admin UI changes for broken flows, hardcoded URLs, and unsafe assumptions
---

Review frontend changes.

Fail the check if any of these are true:
- Public API URL is hardcoded
- Admin/owner/company role assumptions are inconsistent with backend
- Missing loading/error/empty states for critical pages
- UI calls endpoints that do not exist
- Dashboard links point to wrong ports or unsafe public services
- Forms submit invalid payloads without client-side guardrails
- Auth token handling is unsafe

Give exact files, affected page/flow, and suggested fix.