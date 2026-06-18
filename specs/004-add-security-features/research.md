# Security Hardening Research

## 1. Multi-Factor Authentication (MFA)
- **Decision**: Implement Time-based One-Time Password (TOTP) for MFA.
- **Rationale**: TOTP (via apps like Google Authenticator, Authy) is an industry standard, requires no external SMS provider (which costs money and is less secure), and is widely supported by python libraries like `pyotp`.
- **Alternatives considered**: SMS-based MFA (expensive, vulnerable to SIM swapping), WebAuthn/FIDO2 (more complex to implement across both backend and frontend).

## 2. Durable Security Events
- **Decision**: Persist security events to a new PostgreSQL table (`security_events`).
- **Rationale**: Currently, events are either logged to stdout or kept in memory. Persisting them to the relational database allows complex querying (by tenant, severity, date range), which is required by the spec.
- **Alternatives considered**: External logging services like Datadog or ELK stack (adds significant deployment complexity for the current architecture), flat files (hard to query).

## 3. Role Management UI/API
- **Decision**: Extend existing `User` model to allow dynamic role assignment via a dedicated `/admin/roles` endpoint.
- **Rationale**: The project already uses `roles` in JWT and role checking functions (`has_role`). Exposing a secure endpoint to mutate these roles allows platform owners to manage them via the frontend without needing direct database access.
- **Alternatives considered**: External Identity Provider (Okta/Auth0) - rejected because it moves authentication out of the current system, violating the desire to keep it self-contained.

## 4. Abuse Detection and Simulations
- **Decision**: Introduce a middleware or service layer that scans inputs (using existing sanitization patterns) and increments abuse counters per user/IP. Safe simulations will run with a `is_simulation=True` flag that bypasses actual account suspension.
- **Rationale**: Reuses the `InMemoryRateLimiter` and brute-force tracking logic already present, extending it to general input abuse. The simulation flag ensures safe testing.
- **Alternatives considered**: WAF (Web Application Firewall) - a WAF is external to the application and harder to integrate with application-specific simulation logic.
