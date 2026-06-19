# Feature Specification: Security Engineer Dashboard & UI Pages

**Feature Branch**: `005-sec-eng-dashboard`
**Created**: 2026-06-18
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Security Center Access & Layout (Priority: P1)

As a Security Engineer, I want a dedicated "Security Center" view so that I can monitor platform security events and statistics.

**Why this priority**: It is the core hub for security operations. Without it, the security engineer cannot perform their job visually.

**Independent Test**: Can be fully tested by logging in as a user with `security_engineer` role and navigating to the Security Center.

**Acceptance Scenarios**:

1. **Given** I am a `security_engineer`, **When** I click "Security Center" in the sidebar, **Then** I see the main security dashboard with stats and event tabs.
2. **Given** I am a `user` without security roles, **When** I try to navigate to `/admin/security`, **Then** I am redirected and denied access via `RoleGuard`.

---

### User Story 2 - Security Events Feed & Stream (Priority: P1)

As a Security Engineer, I want to see a live feed and historical table of security events to identify suspicious behavior.

**Why this priority**: Vital for incident detection.

**Independent Test**: Can be fully tested by triggering a failed login and seeing it appear in the live feed.

**Acceptance Scenarios**:

1. **Given** the Security Center is open, **When** I view the Events Feed tab, **Then** I see a paginated table fetching from `/security/events`.
2. **Given** the Live Feed panel is visible, **When** a new event occurs backend, **Then** it appears immediately via the SSE stream from `/security/events/stream`.

---

### User Story 3 - Incident Management & Details (Priority: P1)

As a Security Engineer, I want to view, assign, and resolve incidents so that I can manage the security response lifecycle.

**Why this priority**: Required to actually mitigate issues once detected.

**Independent Test**: View an incident, change its status to INVESTIGATING, and observe the state update.

**Acceptance Scenarios**:

1. **Given** I am on the Incidents tab, **When** I click an incident row, **Then** a detailed panel opens fetching from `/incidents/{incident_id}`.
2. **Given** I am viewing an incident, **When** I click "Assign to me", **Then** the incident is assigned to my user ID via `POST /incidents/{incident_id}/assign`.

---

### User Story 4 - Incident Response Actions (Suspend/Block) (Priority: P2)

As a Security Engineer, I want to take direct action (e.g., block, suspend) on malicious actors directly from an incident detail panel.

**Why this priority**: Empowers the engineer to stop active threats.

**Independent Test**: Suspend an actor from an incident and verify their status changes to SUSPENDED.

**Acceptance Scenarios**:

1. **Given** an open incident, **When** I click "Suspend User", **Then** the `POST /incidents/{incident_id}/action` endpoint is called with `suspend_user` action type.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST update frontend `RoleGuard` and `permissions.ts` to recognize `security_engineer`, `cybersecurity_engineer`, and `admin` roles.
- **FR-002**: System MUST add `Security Center` to the navigation sidebar for users with security roles.
- **FR-003**: System MUST implement a high-fidelity, aesthetically premium Security Center Dashboard using modern React components (e.g., shadcn/ui charts, tables).
- **FR-004**: System MUST implement an Events Feed tab calling `GET /security/events` and `GET /security/events/stream`.
- **FR-005**: System MUST implement an Incidents tab calling `GET /incidents`.
- **FR-006**: System MUST implement an Incident Details Drawer/Panel that supports status transitions and notes.
- **FR-007**: System MUST provide Action buttons (Suspend/Block/Restore) within Incident Details that map to `/incidents/{id}/action`.
- **FR-008**: System MUST implement an Attack Simulation button mapping to `POST /security/simulate`.

### Key Entities

- **SecurityEvent**: Contains timestamp, actor, type, severity, and message.
- **Incident**: Contains ID, type, severity, status, actor info, and timeline logs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Security Engineer can log in and view the full Security Center without 403 errors.
- **SC-002**: The Events Feed successfully connects to the SSE stream and renders real-time updates.
- **SC-003**: The UI visually distinguishes between `security_engineer` views and `company_admin` views securely without route leaking.
- **SC-004**: The UI employs premium, dynamic aesthetics with smooth transitions, responsive tables, and intuitive layout.

## Assumptions

- The backend APIs documented in `security/secfront.md` (`/security/events`, `/incidents`, etc.) are fully operational and return the expected payloads.
- The `frontend-next` project is using Tailwind CSS, Radix UI (shadcn), and React Query for data fetching.
