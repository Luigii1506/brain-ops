# Target Architecture

## Architectural shift

The system must evolve from a conversation-centered assistant into a reusable operational core.

The center of the architecture should no longer be:

- intents
- follow-ups
- Telegram/OpenClaw flows

The center should become:

- domains
- use cases
- events
- monitoring
- workflows
- storage boundaries
- reusable APIs

## Target high-level structure

- interfaces/
  - telegram/
  - openclaw/
  - cli/
  - api/

- core/
  - config/
  - logging/
  - validation/
  - routing/
  - execution/
  - events/
  - scheduling/
  - alerts/
  - search/

- domains/
  - personal/
    - nutrition/
    - fitness/
    - expenses/
    - habits/
    - tasks/
    - journal/
  - knowledge/
    - notes/
    - obsidian/
    - summaries/
    - research/
    - linking/
  - monitoring/
    - sources/
    - monitors/
    - snapshots/
    - diffs/
    - alerts/
  - automation/
    - workflows/
    - playbooks/
    - runs/
  - projects/
    - registry/
    - contexts/

- ai/
  - ollama/
  - parsing/
  - extraction/
  - summarization/
  - classification/

- storage/
  - sqlite/
  - obsidian/
  - files/
  - repositories/

## Desired principles

- Interface adapters should depend on use cases, not on domain internals.
- Domain logic should be reusable from CLI, API, Telegram, cron, and OpenClaw.
- Conversation should be treated as one adapter, not the platform center.
- Monitoring and automation must become first-class modules.
- Events should be introduced as a stable internal mechanism.
- Changes should be incremental, not a destructive rewrite.
