# Migration Rules

## Rules Codex must follow

1. Do not rewrite the project from scratch.
2. Prefer incremental refactors.
3. Preserve existing behavior unless explicitly changing it.
4. Extract conversation-specific logic away from the core.
5. Do not break SQLite or Obsidian responsibilities.
6. Do not move structured operational data into Obsidian.
7. Keep OpenClaw as interface/orchestrator, not domain brain.
8. Prefer introducing folders/modules first, then moving files gradually.
9. Avoid premature microservices or distributed architecture.
10. Keep the code ready for future migration from SQLite to PostgreSQL, but do not force that migration now.
11. When proposing changes, explain:

- what is being moved
- why
- what remains compatible
- what should be migrated later

12. When uncertain, choose the smallest safe refactor.
