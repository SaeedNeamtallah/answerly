---
name: Security Review
description: Flag secrets, auth bypasses, unsafe input handling, SQL injection risk, and sensitive logging
---

Review this pull request for security issues.

Fail the check if any of these are true:
- Hardcoded API keys, tokens, credentials, or secrets
- New API endpoints without authentication or authorization checks
- User input reaches SQL, shell commands, file paths, or external requests without validation
- SQL queries are built with string concatenation
- Sensitive data is logged to stdout, files, or monitoring systems
- CORS, auth, webhook, or provider config is weakened
- Docker/compose changes expose Postgres, Redis, Qdrant, RabbitMQ, Prometheus, or Grafana publicly without auth

If none of these issues are found, pass the check.
Give concrete file-level findings and suggested fixes.