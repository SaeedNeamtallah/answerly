---
name: squad-workflow
description: Use when you need to initialize Squad, import a Jira story, or draft a plan before implementation.
---

Start from the current repository and follow the Squad workflow.

1. Run `squad init` if `.squad/` is missing.
2. Run `squad new-story <story-slug> --id <JIRA-ID>` to fetch the Jira issue and write the intake.
3. Run `squad new-plan --api` after intake exists to generate the implementation plan.
4. Read the generated intake and plan before changing code.
5. Keep `.squad/secrets.yaml` local and git-ignored.

Use this workflow only for Jira-backed feature work, structured planning, or when the user explicitly asks for Squad.