---
name: Backend Review
description: Review FastAPI/backend changes for correctness, reliability, and production safety
---

Review backend changes.

Fail the check if any of these are true:
- Route allows access without the required role
- Database transaction can partially commit unsafe side effects
- Celery/task logic can silently fail without status visibility
- External API/provider errors are swallowed
- Webhook/polling logic can double-process events
- Config values are hardcoded instead of read from settings/env
- Missing validation for request payloads
- Missing tests for changed critical flow

Focus on auth, provider config, document upload, search, generation, Telegram webhook, Celery, and observability.