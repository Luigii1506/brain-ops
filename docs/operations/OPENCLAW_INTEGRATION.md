# OpenClaw Integration

## Purpose

This document defines the contract between OpenClaw and `brain-ops`.

OpenClaw should treat `brain-ops` as the deterministic execution layer.
It should not replicate routing logic, vault rules, or SQLite write logic outside this project.

## Integration model

```text
Telegram
  |
  v
OpenClaw chat / agent
  |
  v
brain-ops CLI
  |
  v
Obsidian Vault + SQLite
```

## Core rule

Telegram is the primary end-user chat channel.
OpenClaw is the agent/orchestration layer behind that channel.

OpenClaw should prefer calling:
- `brain handle-input --json`
- `brain handle-input --json --session-id <stable-session-id>`

This is the primary natural-language entrypoint.

OpenClaw should only call domain-specific commands directly when:
- the user is already in a structured workflow,
- the required fields are explicit,
- or deterministic execution is clearly better than natural-language routing.

## Primary tool entrypoints

### 1. Natural input
- `brain handle-input --json`
- For Telegram/OpenClaw, the plugin must always send a stable session id so `brain-ops` can resolve follow-ups like `sí`, `no`, `resumen` or `objetivos` against the last pending question.

Use when:
- the user speaks naturally,
- the input may contain one or multiple safe actions,
- the system should decide the right domain/command.

Expected output fields:
- `intent`
- `intent_version`
- `executed`
- `executed_command`
- `target_domain`
- `routing_source`
- `confidence`
- `extracted_fields`
- `normalized_fields`
- `needs_follow_up`
- `follow_up`
- `assistant_message`
- `sub_results`

### 2. Classification only
- `brain route-input --json`

Use when:
- OpenClaw wants a plan without side effects,
- the system should preview the likely action before execution.

### 3. Daily memory sync
- `brain daily-summary`

Use when:
- daily structured data should be written into Obsidian,
- end-of-day or periodic summarization runs.

## Output interpretation

### Successful single action
If:
- `executed: true`
- `executed_command != "multi-action"`

Then OpenClaw should:
- trust the action result,
- surface `assistant_message`,
- optionally inspect `extracted_fields`.

### Successful multi-action
If:
- `executed: true`
- `executed_command == "multi-action"`

Then OpenClaw should:
- surface `assistant_message`,
- iterate `sub_results`,
- summarize each executed sub-action in chat or UI,
- avoid re-running the same clauses.

### Follow-up required
If:
- `executed: false`
- `needs_follow_up: true`

Then OpenClaw should:
- ask a clarification question,
- use `follow_up` as the base suggestion,
- avoid guessing missing required fields.

## Routing source semantics

- `heuristic`
  The deterministic parser handled the input directly.

- `llm`
  A local model produced the routing result.

- `hybrid`
  Heuristic and LLM were both consulted and arbitration decided the final route.

OpenClaw should treat `heuristic` and `hybrid` as higher-trust execution paths than unconstrained freeform generation.

## Current operational setup

- Channel: Telegram
- Main model: `ollama/qwen3.5:9b`
- Main tool policy: minimal profile with `brain_ops_handle_input` as the primary tool
- Stable follow-up session id inside the plugin: `telegram-main`

### Enabled hooks

- `command-logger`
  Purpose: keep an audit trail of command-level activity.
- `session-memory`
  Purpose: preserve useful context when starting fresh sessions with `/new`.

### Active cron jobs

- `jarvis-manana`
  Schedule: `0 8 * * *` in `America/Tijuana`
  Purpose: send a short morning summary to Telegram with status and pending items.
- `jarvis-noche`
  Schedule: `0 21 * * *` in `America/Tijuana`
  Purpose: send a short night review to Telegram with progress, gaps, and next action.

## Deferred OpenClaw enhancements

- `memory-lancedb`
  Consider only if core memory search becomes insufficient.
- `llm-task`
  Consider for isolated structured subtasks inside OpenClaw, not as a replacement for `brain-ops`.
- `voice-call`
  Consider later only if phone-call interaction becomes more valuable than Telegram voice notes.

## Recommended OpenClaw tool set

Expose these first:
- `handle_input`
- `route_input`
- `daily_summary`
- `daily_macros`
- `daily_habits`
- `workout_status`
- `spending_summary`
- `body_metrics_status`
- `capture`
- `improve_note`
- `research_note`

## Direct command mapping

Suggested mappings:

- `handle_input`
  `brain handle-input "<text>" --json`

- `route_input`
  `brain route-input "<text>" --json`

- `daily_summary`
  `brain daily-summary --date <yyyy-mm-dd>`

- `daily_macros`
  `brain daily-macros --date <yyyy-mm-dd>`

- `daily_habits`
  `brain daily-habits --date <yyyy-mm-dd>`

- `workout_status`
  `brain workout-status --date <yyyy-mm-dd>`

- `spending_summary`
  `brain spending-summary --date <yyyy-mm-dd>`

- `body_metrics_status`
  `brain body-metrics-status --date <yyyy-mm-dd>`

## What OpenClaw should not do

- do not write directly to the vault
- do not write directly to SQLite
- do not reimplement note ontology rules
- do not decide destination folders independently
- do not mutate Markdown outside `brain-ops`
- do not treat external skills as the source of truth

## Future plugin direction

The preferred long-term path is:
- a project-owned OpenClaw plugin/skill for `brain-ops`

That plugin should:
- expose the commands above as tools,
- pass through JSON responses,
- keep OpenClaw thin and `brain-ops` authoritative.

## Integration assets

Project-owned integration assets live in:
- [integrations/openclaw/README.md](/Users/luisencinas/Documents/GitHub/brain-ops/integrations/openclaw/README.md)
- [integrations/openclaw/manifest.json](/Users/luisencinas/Documents/GitHub/brain-ops/integrations/openclaw/manifest.json)
- [.openclaw/extensions/brain-ops/README.md](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/README.md)
- [.openclaw/extensions/brain-ops/openclaw.plugin.json](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/openclaw.plugin.json)
- [.openclaw/extensions/brain-ops/index.ts](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/index.ts)
