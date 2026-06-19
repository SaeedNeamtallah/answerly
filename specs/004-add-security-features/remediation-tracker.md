# Remediation Tracker: Final Security Hardening

Date: 2026-06-18

This tracker records the remediation work added after the original T003-T033 validation pass. The original 31-point validation items were already marked complete; the items below cover the hardening gaps and test drift found during final implementation.

## Remediated Items

| ID | Finding | Remediation | Evidence |
| --- | --- | --- | --- |
| R-001 | Legacy `GET /bot/config` could expose raw configuration without authentication. | `backend/routes/bot_config.py` now requires `get_current_db_user`, validates owned `active_project_id`, and returns only `active_project_id`, `legacy`, and `warning`. | `test_bot_config_read_requires_authenticated_user_dependency`, `test_bot_config_read_returns_public_safe_fields_only` |
| R-002 | Privileged MFA existed for setup/verify, but privileged access could proceed without an MFA-verified session. | Privileged login returns `mfa_required` or `mfa_setup_required`; privileged dependencies enforce MFA enrollment plus `mfa_verified` JWT claim. | `test_privileged_platform_owner_without_mfa_is_denied`, `test_privileged_platform_owner_requires_mfa_verified_token`, `test_privileged_platform_owner_with_verified_mfa_is_allowed` |
| R-003 | Recovery codes were generated as plain values and were not consumed on use. | `MFAService` hashes recovery codes, verifies legacy/plain or hashed codes, and consumes matched codes exactly once. | `test_recovery_codes_are_hashed_and_one_time_use`, `test_mfa_verify_persists_hashed_recovery_codes` |
| R-004 | Persisted security events needed explicit retention/indexing and simulation/delivery fields. | `SecurityEventRecord` has `is_simulation`, `delivery_status`, and compound indexes; retention defaults to `SECURITY_EVENT_RETENTION_DAYS=180`. | `test_security_event_model_has_retention_indexes_and_delivery_fields` |
| R-005 | Security Center views needed DB-backed event data and exportable simulation/delivery state. | Dashboard, CSV export, and SSE payloads are backed by `list_events(db=...)`; response models include `is_simulation` and `delivery_status`. | Full backend test suite plus report evidence |
| R-006 | Suspicious input detection could miss stripped script payloads and risk storing snippets. | Detection now checks raw input before sanitization and records redacted category/hash evidence only. | `test_suspicious_input_logs_redacted_event` |
| R-007 | Destructive simulations could choose an implicit fallback target. | Destructive simulation now requires explicit `target_user_id`, platform-owner access, and `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED=true`. | `test_security_simulation_destructive_mode_requires_explicit_target` |
| R-008 | Role management could demote the last platform owner and lacked a general audit-log row. | Role changes now block last-platform-owner demotion and write `RoleAssignmentHistory`, `AuditLog`, and `ROLE_ASSIGNMENT_CHANGED` security events. | `test_role_management_prevents_last_platform_owner_demotion`, `test_role_assignment_writes_history_and_audit_log` |
| R-009 | Production CORS validation only rejected localhost origins. | Production validation rejects wildcard, localhost, non-HTTP(S), and plain HTTP origins. | `test_production_secret_validation_rejects_wildcard_cors_origin`, `test_production_secret_validation_rejects_http_cors_origin`, `test_production_secret_validation_allows_https_frontend_cors_origin` |
| R-010 | Full backend tests exposed a stale `CustomerBotQueryService` test/controller compatibility issue for optional custom prompts. | `custom_system_prompt` is only passed when configured on the integration. | Full backend suite: `108 passed` |

## Open Remediation

None from T003-T033 remain open after the final hardening pass.
