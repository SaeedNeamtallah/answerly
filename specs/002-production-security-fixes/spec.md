# Feature Specification: Production Security Fixes

**Feature Branch**: `002-production-security-fixes`  
**Created**: 2026-04-29
**Status**: Draft  
**Input**: User description: "Production readiness fixes based on review: P0 secrets exposed, weak JWT default, uncommitted Telegram replies, unsafe Simulation endpoint, token in localStorage, JSON concurrency, context bloating..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Secrets and Configurations (Priority: P1)

As a system administrator, I want the application to fail fast if default insecure secrets are used and to read secrets from environment variables that are never committed, so that the application is protected against unauthorized access.

**Why this priority**: Leaving default secrets or exposing real API keys is a P0/P1 security risk that can lead to account takeover and data breaches.

**Independent Test**: Can be fully tested by starting the application without `AUTH_JWT_SECRET_KEY` set or set to `change-me-in-env` in production mode and verifying that the backend fails to start.

**Acceptance Scenarios**:

1. **Given** the environment is set to production and `AUTH_JWT_SECRET_KEY` is not provided or weak, **When** the backend starts, **Then** the backend crashes with a clear validation error.
2. **Given** the `.env` file contains no sensitive real API keys, **When** pushing code, **Then** secret scanners do not detect any leaked credentials.

---

### User Story 2 - Transactional Outbox for Telegram Replies (Priority: P1)

As a Telegram user, I want my interactions with the bot to be reliable, so that I don't receive duplicate responses or lose conversation history due to server crashes.

**Why this priority**: Sending a response to a third-party API before committing the action to the local database leads to split-brain scenarios and data inconsistency (P1).

**Independent Test**: Can be fully tested by deliberately injecting a failure after a message is queued but before the worker processes it, verifying no duplicate messages are sent.

**Acceptance Scenarios**:

1. **Given** an incoming Telegram webhook request, **When** the system determines a response, **Then** the message is saved as `pending` in the database and the HTTP request returns successfully.
2. **Given** a `pending` message in the database, **When** the worker processes it, **Then** the message is sent to Telegram, marked as `sent`, and the `telegram_message_id` is recorded.

---

### User Story 3 - Safe Security Simulation (Priority: P1)

As an administrator using the Security Center simulation endpoint, I want the simulation to be non-destructive by default, so that I do not accidentally block real users while testing.

**Why this priority**: A simulation endpoint that can block real users is a high-risk operational danger (P1).

**Independent Test**: Can be fully tested by running a security simulation without explicit destructive flags and verifying that no user accounts are suspended or blocked.

**Acceptance Scenarios**:

1. **Given** a platform owner runs a standard simulation, **When** the simulation executes, **Then** it generates audit logs but no users are actually blocked.
2. **Given** a non-platform-owner attempts to run a destructive simulation, **When** the API is called, **Then** a 403 Forbidden error is returned.

---

### User Story 4 - Secure Frontend State (Priority: P1)

As a user, I want my session to be secure from XSS attacks, so that malicious scripts cannot steal my authentication token.

**Why this priority**: Storing JWT tokens in `localStorage` alongside widespread `innerHTML` usage creates a high risk of complete account takeover (P1).

**Independent Test**: Can be fully tested by verifying that authentication uses `HttpOnly`, `Secure`, `SameSite` cookies rather than `localStorage`.

**Acceptance Scenarios**:

1. **Given** a successful login, **When** the frontend receives the token, **Then** the token is stored in an `HttpOnly` cookie or memory, not `localStorage`.
2. **Given** the frontend rendering process, **When** displaying user input, **Then** `innerHTML` is avoided or rigorously sanitized with a strict CSP.

---

### User Story 5 - Reliable Runtime Configuration (Priority: P2)

As a system, I want runtime configurations to be read and written safely in concurrent environments, so that configuration data isn't corrupted or lost.

**Why this priority**: Concurrent file writes to a JSON file without locks can corrupt the system configuration (P1/P2).

**Independent Test**: Can be fully tested by simulating multiple concurrent updates to the runtime config and verifying the final state is consistent.

**Acceptance Scenarios**:

1. **Given** multiple concurrent requests to update configuration, **When** the updates process, **Then** either file-level locks, atomic renames, or database storage ensures no writes are lost or corrupted.

---

### Edge Cases

- What happens when a Telegram webhook is received but the database is temporarily unavailable?
- How does the system handle an API request if the config file is locked for writing by another process?
- What happens when a document chunks parent-content would exceed the LLM's maximum token limit?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST strictly validate `AUTH_JWT_SECRET_KEY` and other sensitive defaults upon startup, failing immediately in production if weak values are detected.
- **FR-002**: System MUST NOT expose the application directly on port 8000 in production documentation/configurations without a reverse proxy.
- **FR-003**: System MUST implement a Transactional Outbox pattern for Telegram messaging, ensuring database commits happen before external API calls.
- **FR-004**: System MUST ensure the Security Center simulation is non-destructive by default and requires explicit `platform_owner` permissions for destructive actions.
- **FR-005**: System MUST utilize `HttpOnly` cookies for authentication tokens instead of `localStorage`.
- **FR-006**: System MUST ensure concurrent updates to runtime configuration are thread-safe (e.g., atomic rename, file lock, or DB migration).
- **FR-007**: System MUST impose a defined token budget for context generation during RAG queries to prevent context bloat.
- **FR-008**: System MUST deduplicate `parent_content` across child chunks to reduce database storage bloat.
- **FR-009**: System MUST consolidate document processing paths, removing unused or duplicated implementations in `DocumentController`.
- **FR-010**: System MUST NOT expose `GET /config/providers` to unauthenticated or unauthorized users if it contains sensitive internal choices.
- **FR-011**: System MUST output structured JSON logs including `request_id` for enhanced observability.

### Key Entities

- **PendingMessage** (or Outbox Message): Represents a Telegram message that is scheduled to be sent.
- **RuntimeConfig**: The application configuration, which should be safely updated and versioned.
- **ParentChunk**: Represents the extracted parent text to avoid duplicating it across all child chunk metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Security scanners report 0 exposed secrets in the git repository history and `.env` files.
- **SC-002**: The application refuses to start in production mode if the JWT secret length is insufficient or is set to default.
- **SC-003**: 100% of Telegram bot replies are processed via an outbox queue, avoiding split-brain duplicates.
- **SC-004**: Security simulation endpoints return 0 actual user suspensions when run without explicitly enabling destructive flags.
- **SC-005**: No JWT tokens are found in the browser's `localStorage` after authentication.

## Assumptions

- We assume we can safely change the Telegram bot reply mechanism to an asynchronous worker without breaking the user experience.
- We assume moving to `HttpOnly` cookies will not break API clients that expect a Bearer token, or we will support both modes conditionally (e.g., cookies for browsers, Bearer for API clients).
- We assume that removing the duplicated path in `DocumentController` will not affect any active processes.
