# Non-Negotiables

These are hard architectural rules for this repository.

## Independence and resilience

1. The core system must continue to function even if OpenClaw is unavailable.
2. The core system must continue to function even if Telegram is unavailable.
3. The core system must continue to function even if Obsidian is temporarily unavailable.
4. The core system should continue to support deterministic operations even if Ollama is unavailable.
5. Interfaces are optional surfaces; the operational core is the real product.

## Role boundaries

6. OpenClaw is an orchestrator/interface layer, not the business brain.
7. Telegram is an input/output surface, not the center of the architecture.
8. Obsidian is a durable knowledge/documentation layer, not the main transactional store.
9. SQLite is the current operational structured store.
10. brain-ops is the true operational core.

## Architectural direction

11. The project is evolving into a reusable mother project / operational core.
12. The architecture must support both personal use cases and future reusable modules/APIs.
13. The architecture must be centered on capabilities, domains, events, workflows, and storage boundaries, not on chat flows.
14. Monitoring, automation, alerts, snapshots, and reusable APIs are first-class future capabilities.
15. Refactors must be incremental and safe.

## Reliability

16. Critical operations should not depend on LLM availability.
17. The system should degrade gracefully when optional layers are unavailable.
18. Domain logic should be reusable from CLI, API, cron jobs, Telegram, and OpenClaw.
