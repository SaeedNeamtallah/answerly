# Security Features Data Model

## Entities

### `User` (Modifications)
- **New Fields**:
  - `mfa_secret` (String, Nullable): The TOTP secret for the user. If null, MFA is not enrolled.
  - `mfa_enabled` (Boolean): Whether MFA is actively enforced for this user.
  - `mfa_recovery_codes` (JSONB, Nullable): Hashed recovery codes for account recovery.

### `SecurityEvent` (New Entity)
- **Fields**:
  - `id` (Integer, Primary Key)
  - `event_type` (String, Indexed): e.g., 'LOGIN_FAIL', 'BRUTE_FORCE', 'AUTHZ_DENIED', 'SUSPICIOUS_INPUT'
  - `severity` (String): e.g., 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
  - `actor_id` (Integer, Nullable, Foreign Key to User): The user who triggered the event, if known.
  - `tenant_id` (Integer, Nullable, Foreign Key to Project/Tenant): The associated tenant context.
  - `timestamp` (DateTime, Indexed): When the event occurred.
  - `ip_address` (String, Nullable): Source IP.
  - `message` (Text): Human-readable description.
  - `metadata_json` (JSONB): Additional context, redacted as necessary.
  - `is_simulation` (Boolean): Flag to distinguish real events from simulated tests.
  - `delivery_status` (String): e.g., 'PENDING', 'DELIVERED', 'FAILED' (for external monitoring).

### `RoleAssignmentHistory` (New Entity)
- **Fields**:
  - `id` (Integer, Primary Key)
  - `target_user_id` (Integer, Foreign Key to User)
  - `actor_user_id` (Integer, Foreign Key to User): The admin who made the change.
  - `previous_role` (String)
  - `new_role` (String)
  - `reason` (Text, Nullable)
  - `timestamp` (DateTime)

## Contracts / API Endpoints

### MFA Endpoints
- `POST /auth/mfa/setup`: Generates a TOTP secret and QR code for the current user.
- `POST /auth/mfa/verify`: Verifies a TOTP token to complete setup or login.
- `POST /auth/mfa/recovery`: Generates or consumes recovery codes.

### Security Center Endpoints
- `GET /admin/security/events`: Retrieves paginated, filtered security events (severity, tenant, date range).
- `POST /admin/security/events/export`: Generates a sanitized export of security events.
- `POST /admin/security/simulate`: Triggers a security simulation with a specific scenario payload.

### Role Management Endpoints
- `GET /admin/roles/users`: Lists users and their current roles.
- `PUT /admin/roles/users/{user_id}`: Updates a user's role, recording the change in history.
