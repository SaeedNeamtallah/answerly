# Contract: UI Block Upgrade

This contract applies to every block upgraded under the incremental UI/UX feature.

## Required Inputs

- Block id and owning route.
- Existing components used by the block.
- Existing API calls, query keys, mutations, and role guards.
- Primary user task supported by the block.
- Target screenshot pattern or design pattern.

## Preservation Requirements

- Existing primary actions remain available.
- Existing backend payload shapes remain unchanged unless another approved task changes the backend contract.
- Existing auth and role visibility remain unchanged.
- Existing loading, empty, error, disabled, and success states remain represented.
- Existing destructive-action safeguards remain present.
- Existing user-facing domain concepts remain recognizable.

## Upgrade Requirements

- Visual hierarchy must be clearer than the previous block.
- Controls must use established shadcn/ui components before custom markup.
- Icons must come from Lucide where available.
- Tables that need sorting, filtering, pagination, selection, or column actions should use the shared TanStack Table layer.
- Forms with validation should use React Hook Form and Zod.
- Charts should use shadcn chart wrappers and Recharts.
- Status must use consistent badge/progress semantics.
- Long text, long labels, and partial data must not break layout.

## Review Checklist

- Route still loads for the intended role.
- Primary action still works.
- Related API calls still use the existing auth token path.
- No unrelated route blocks changed in the same review unless explicitly listed.
- Desktop, tablet, and mobile widths were checked.
- Keyboard focus order and visible focus were checked for interactive controls.
- Error and empty states were checked or intentionally marked not applicable.
- Lint and typecheck pass after the block.

## Done Definition

A block is done only when it is visually upgraded, behavior-preserving, validated, and documented in the implementation notes or task output.
