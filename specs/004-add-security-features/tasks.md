# Implementation Tasks: Additional Security Hardening

**Feature**: `004-add-security-features`
**Generated**: 2026-06-17

## Phase 1: Setup & Foundational Prerequisites
- [x] T001 Update environment variables (`.env.example`) to include `AUTH_MFA_ISSUER` and database paths.
- [x] T002 Configure Playwright/E2E test setup for handling MFA forms.

## Phase 2: Validate Existing Security Features (User Requested)
**Goal**: Iterate over the 31 points listed in `securityfeatures.md` to ensure they are correctly integrated and functioning in the VM-deployed project before adding new features. Subagents can be spawned for these points.
- [x] T003 [P] [US-Validation] Validate Point 1: Security configuration layer (`backend/config.py`)
- [x] T004 [P] [US-Validation] Validate Point 2: JWT authentication (`backend/security/jwt_utils.py`)
- [x] T005 [P] [US-Validation] Validate Point 3: Password security (`backend/services/auth_service.py`)
- [x] T006 [P] [US-Validation] Validate Point 4: Username validation and normalization
- [x] T007 [P] [US-Validation] Validate Point 5: Service account security
- [x] T008 [P] [US-Validation] Validate Point 6: Role-Based Access Control (`backend/security/auth.py`)
- [x] T009 [P] [US-Validation] Validate Point 7: Account status enforcement
- [x] T010 [P] [US-Validation] Validate Point 8: Login brute-force protection
- [x] T011 [P] [US-Validation] Validate Point 9: Rate limiting (`backend/security/middleware.py`)
- [x] T012 [P] [US-Validation] Validate Point 10: Input sanitization
- [x] T013 [P] [US-Validation] Validate Point 11: Filename sanitization
- [x] T014 [P] [US-Validation] Validate Point 12: File upload security
- [x] T015 [P] [US-Validation] Validate Point 13: Project ownership isolation
- [x] T016 [P] [US-Validation] Validate Point 14: Document ownership isolation
- [x] T017 [P] [US-Validation] Validate Point 15: Query/RAG access control
- [x] T018 [P] [US-Validation] Validate Point 16: Vector database security
- [x] T019 [P] [US-Validation] Validate Point 17: Background task security
- [x] T020 [P] [US-Validation] Validate Point 18: Security event logging
- [x] T021 [P] [US-Validation] Validate Point 19: Incident management system
- [x] T022 [P] [US-Validation] Validate Point 20: Incident lifecycle enforcement
- [x] T023 [P] [US-Validation] Validate Point 21: Incident response actions
- [x] T024 [P] [US-Validation] Validate Point 22: Admin user controls
- [x] T025 [P] [US-Validation] Validate Point 23: Security Center dashboard APIs
- [x] T026 [P] [US-Validation] Validate Point 24: Security event CSV export
- [x] T027 [P] [US-Validation] Validate Point 25: Attack simulation / SOC demo mode
- [x] T028 [P] [US-Validation] Validate Point 26: Frontend security behavior
- [x] T029 [P] [US-Validation] Validate Point 27: Runtime configuration security
- [x] T030 [P] [US-Validation] Validate Point 28: Bot configuration security
- [x] T031 [P] [US-Validation] Validate Point 29: Error handling hardening
- [x] T032 [P] [US-Validation] Validate Point 30: CORS hardening
- [x] T033 [P] [US-Validation] Validate Point 31: Operational security / availability checks

## Phase 3: User Story 1 (Protect Privileged Sign-In With MFA)
**Goal**: Require TOTP for admins and security engineers.
- [x] T034 [US1] Create migration for mfa_secret, mfa_enabled, and mfa_recovery_codes in User model
- [x] T035 [US1] Implement MFAService with pyotp in backend/services/mfa_service.py
- [x] T036 [US1] Create MFA setup and verification endpoints in backend/routes/auth_mfa.py
- [x] T037 [US1] Build MFA Setup UI page in frontend-next/src/app/(auth)/mfa/setup/page.tsx
- [x] T038 [US1] Build MFA Verification UI page in frontend-next/src/app/(auth)/mfa/verify/page.tsx

## Phase 4: User Story 2 (Preserve Security Evidence Across Restarts)
**Goal**: Persist security events to the database instead of in-memory.
- [x] T039 [US2] Create migration for `security_events` table.
- [x] T040 [US2] Update `SecurityEvent` model in `backend/database/models.py`.
- [x] T041 [US2] Update `EventService` to write to PostgreSQL instead of in-memory queue in `backend/security/event_service.py`.

## Phase 5: User Story 3 (Manage Security Roles And Protected Configuration Safely)
**Goal**: Allow platform owners to manage roles dynamically via UI.
- [x] T042 [US3] Create migration for `role_assignment_history` table.
- [x] T043 [US3] Create `admin_roles.py` router with update user role endpoints.
- [x] T044 [US3] Build Role Management UI in `frontend-next/src/components/admin/RoleManagement.tsx`.

## Phase 6: User Story 4 (Detect Abuse Attempts And Run Safe Simulations)
**Goal**: Detect suspicious input and flag simulations appropriately.
- [x] T045 [US4] Add middleware or logic in `backend/security/sanitization.py` to flag XSS/SQLi as `SUSPICIOUS_INPUT` events.
- [x] T046 [US4] Ensure `simulate_security_attack` sets `is_simulation=True` in DB records.

## Final Phase: Polish & Cross-Cutting Concerns
- [x] T047 Perform End-to-End deployment smoke test on the VM with the new features.
