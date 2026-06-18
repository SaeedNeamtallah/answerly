# Implementation Plan: Additional Security Hardening

**Branch**: `004-add-security-features` | **Date**: 2026-06-17 | **Spec**: [spec.md](file:///C:/Users/saeid/github%20projects/ragmind%20discussed/specs/004-add-security-features/spec.md)
**Input**: Feature specification from `specs/004-add-security-features/spec.md`

## Summary

This plan outlines the integration of multi-factor authentication (MFA) for privileged accounts, persistent security events with an audit trail, dynamic UI-based role management, and simulation capabilities for detecting abuse attempts. The backend will be extended using FastAPI and SQLAlchemy, and the frontend will introduce new pages in the Next.js `(admin)` and `(company)` zones.

## Technical Context

**Language/Version**: Python 3.11, TypeScript (Next.js)
**Primary Dependencies**: FastAPI, pyotp (new), SQLAlchemy, Next.js, TanStack Query
**Storage**: PostgreSQL
**Testing**: pytest, Playwright
**Target Platform**: Linux server, Azure Container Apps
**Project Type**: Web Service + Web Application
**Performance Goals**: Negligible latency added to existing authentication and authorization checks.
**Constraints**: Security events must not leak secrets; MFA must not block valid users with proper backup strategies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No rules from the constitution violate the current design. The library-first and test-first principles apply to the new security modules.

## Project Structure

### Documentation (this feature)

```text
specs/004-add-security-features/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/ (Update User, add SecurityEvent, RoleAssignmentHistory)
│   ├── services/ (Add MFAService, SecurityEventService)
│   └── routes/ (Add auth_mfa.py, admin_roles.py)
└── tests/
    └── integration/ (Add test_mfa.py, test_security_events.py)

frontend-next/
├── src/
│   ├── app/
│   │   ├── (auth)/mfa/ (MFA setup/verification flow)
│   │   └── (admin)/security/ (Security Center pages)
│   ├── components/
│   │   └── admin/ (Role management UI, Event viewer)
│   └── lib/api/ (Update auth endpoints, add security endpoints)
```

**Structure Decision**: Web application layout. Modifies existing `backend/` and `frontend-next/` directories.
