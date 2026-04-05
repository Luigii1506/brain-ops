# Codex Working Style

## How to operate on this repository

- Work in small, reviewable steps.
- First analyze the current structure before changing files.
- Propose a migration plan before large refactors.
- Prefer creating new modules and adapting imports over large in-place rewrites.
- Keep naming explicit and domain-oriented.
- Avoid creating vague abstractions unless they solve a real structural issue.
- Keep folder names and module names aligned with architecture intent.
- Use clear comments only where they help future maintainability.
- Favor use cases / application services over intent-driven business logic.

## Expected output style

For each task:

1. summarize current state
2. explain proposed change
3. implement the smallest useful step
4. list follow-up tasks
