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

This is the primary natural-language entrypoint.

OpenClaw should only call domain-specific commands directly when:
- the user is already in a structured workflow,
- the required fields are explicit,
- or deterministic execution is clearly better than natural-language routing.

## Primary tool entrypoints

### 1. Natural input
- `brain handle-input --json`

Use when:
- the user speaks naturally,
- the input may contain one or multiple safe actions,
- the system should decide the right domain/command.

Expected output fields:
- `executed`
- `executed_command`
- `target_domain`
- `routing_source`
- `extracted_fields`
- `needs_follow_up`
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
