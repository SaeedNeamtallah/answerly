# Copilot Instructions

When a task needs Squad intake or planning, use the Squad workflow before editing code:

1. Run `squad init` if `.squad/` is missing.
2. Run `squad new-story <story-slug> --id <JIRA-ID>` to import the Jira story and write the intake.
3. Run `squad new-plan --api` to draft the implementation plan after intake is ready.
4. Read the generated intake and plan files before making code changes.
5. Keep `.squad/secrets.yaml` local and git-ignored.

Use this workflow for Jira-backed feature work, implementation planning, or any task that needs a structured intake before coding.