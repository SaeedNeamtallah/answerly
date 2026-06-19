# Implementation Plan: Security Engineer Dashboard & UI Pages

**Branch**: `005-sec-eng-dashboard` | **Date**: 2026-06-18 | **Spec**: [spec.md](file:///c:/Users/saeid/github%20projects/ragmind%20discussed/specs/005-sec-eng-dashboard/spec.md)

## Summary

The objective is to implement the frontend UI pages for the Security Engineer based on `security/secfront.md`. This involves updating frontend permissions to recognize the new roles, adding the Security Center to the navigation, and building out the complex Dashboard, Events Feed, Incidents Tab, and Incident Details Panel with high aesthetic quality and professional integration with the backend APIs.

## Technical Context

**Language/Version**: TypeScript / React (Next.js App Router)
**Primary Dependencies**: Next.js, Tailwind CSS, shadcn/ui, TanStack React Query
**Storage**: localStorage (for auth tokens)
**Testing**: Playwright for E2E (browser testing UI rendering)
**Target Platform**: Web Browser
**Project Type**: Next.js Web Application
**Performance Goals**: Instant client-side navigation, fast SSE stream rendering.
**Scale/Scope**: ~10 screens/views for Security Engineers.

## Phase 0: Research & Preparation

- [x] Verify backend API endpoints exist and map to the frontend expectations. (Completed via Audit Batch 2 & 3).
- [ ] Research missing components in `shadcn/ui` (e.g. Data Table for incidents).

## Phase 1: Data Model & API Contracts

We will define standard API client functions in `frontend-next/src/lib/api/security.ts` and `frontend-next/src/lib/api/incidents.ts` covering:
- `GET /security/stats`
- `GET /security/events`
- `GET /security/events/stream`
- `GET /incidents`
- `GET /incidents/{id}`
- `POST /incidents/{id}/action`

## Phase 2: Execution Tasks

1. **Auth & Permissions Update**:
   - Update `frontend-next/src/lib/auth/permissions.ts` to support `security_engineer` and `admin`.
   - Update `RoleManagement.tsx` to include the full list of roles.
2. **Layout & Navigation**:
   - Update Sidebar components to show the `Security Center` item for allowed roles.
3. **Security Dashboard Foundation**:
   - Create `frontend-next/src/app/(company)/security/page.tsx` as the main hub.
   - Design high-level summary cards (Stats).
4. **Events Feed**:
   - Build a paginated data table component for events.
   - Integrate SSE stream to push new events into the table dynamically.
5. **Incidents Management**:
   - Build the incidents data table.
   - Build the Incident Details Drawer/Panel component to show logs, actor info, and notes.
6. **Actions & Simulation**:
   - Implement action buttons (Suspend, Block) with confirmation dialogs.
   - Implement the "Simulate Attack" button to trigger the backend simulation route.
7. **Refinement & Aesthetics**:
   - Ensure a premium, dark-mode compatible design.
   - Apply micro-animations and proper loading states.

## Verification

- E2E tests for the Security Engineer role.
- Manual verification of role switching and route protections.
