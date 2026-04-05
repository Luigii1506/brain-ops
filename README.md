# brain-ops

`brain-ops` is the local-first operations layer for a personal Jarvis-style system.

It sits between:
- an Obsidian vault used as the long-term knowledge and documentation layer,
- local AI orchestration through OpenClaw and Ollama,
- and structured local data stored in SQLite for life tracking domains like nutrition, fitness, expenses, and daily logs.

## What this project is really for

This project exists so one user can run a serious personal operating system from a Mac mini:

- capture knowledge without writing everything manually,
- turn raw input into structured notes,
- maintain project documentation and technical runbooks,
- track personal operations like diet, gym, expenses, and habits,
- retrieve context later through Obsidian and AI,
- keep everything local, reviewable, and extensible.

## Core architecture

```text
OpenClaw chat / automations
        |
        v
   Ollama local models
        |
        v
      brain-ops
   /            \
  v              v
Obsidian Vault   SQLite
knowledge        structured life-ops data
```

## System roles

### Obsidian
Human-facing memory and navigation layer.

Use it for:
- knowledge notes
- source notes
- maps of content
- project context
- systems documentation
- reflections
- summaries and reports

### SQLite
Structured operational data layer.

Use it for:
- meals and macros
- workouts and sets
- expenses
- body metrics
- daily structured logs

### brain-ops
Deterministic execution and transformation layer.

Use it to:
- create and normalize notes
- process inbox
- improve notes
- enrich notes with grounded research
- promote source material into durable knowledge
- suggest and apply links
- initialize and later query local structured data

### OpenClaw + Ollama
Conversation and local AI orchestration layer.

Use them to:
- receive natural language input
- parse ambiguous intent into structured actions
- decide which `brain-ops` command to run
- call local models
- keep the system usable without cloud dependencies

## Current natural-language pipeline

`brain-ops` now uses a hybrid intent pipeline:

1. heuristic routing for obvious inputs
2. typed Pydantic intents as the internal contract
3. optional Ollama structured parsing for ambiguous inputs
4. deterministic execution against Obsidian or SQLite

This keeps simple inputs fast and predictable while making room for richer local AI parsing on the Mac mini.

## Current project direction

This is not just a notes app and not just a CLI.

It is a local personal operating system composed of:
- a second brain,
- a documentation engine,
- a life-tracking data backend,
- and an AI interaction layer.

## Current commands

- `brain info`
- `brain init`
- `brain init-db`
- `brain log-meal`
- `brain daily-macros`
- `brain set-macro-targets`
- `brain macro-status`
- `brain create-diet-plan`
- `brain set-active-diet`
- `brain active-diet`
- `brain diet-status`
- `brain log-supplement`
- `brain habit-checkin`
- `brain daily-habits`
- `brain set-habit-target`
- `brain habit-status`
- `brain log-body-metrics`
- `brain body-metrics-status`
- `brain log-workout`
- `brain workout-status`
- `brain log-expense`
- `brain spending-summary`
- `brain set-budget-target`
- `brain budget-status`
- `brain daily-log`
- `brain daily-summary`
- `brain route-input`
- `brain handle-input`
- `brain openclaw-manifest`
- `brain create-note`
- `brain create-project`
- `brain process-inbox`
- `brain weekly-review`
- `brain audit-vault`
- `brain normalize-frontmatter`
- `brain capture`
- `brain improve-note`
- `brain research-note`
- `brain link-suggestions`
- `brain apply-link-suggestions`
- `brain promote-note`
- `brain enrich-note`

## Design principles

- local-first
- Obsidian-compatible
- Markdown-first for knowledge
- SQLite-first for structured operational tracking
- agent-assisted, not agent-chaotic
- reversible and auditable
- CLI-first
- Mac mini as primary node
- OpenClaw + Ollama as default AI stack

## What does not belong in the vault

- production secrets
- API keys
- raw database dumps
- bulky generated artifacts
- machine-only clutter
- high-frequency numeric logs that should live in SQLite first

## Where to start

Read:
- [docs/setup/MAC_MINI_SETUP.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/setup/MAC_MINI_SETUP.md)
- [docs/MASTER_PLAN.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/MASTER_PLAN.md)
- [docs/PRODUCT_VISION.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/PRODUCT_VISION.md)
- [docs/architecture/SYSTEM_ARCHITECTURE.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/architecture/SYSTEM_ARCHITECTURE.md)
- [docs/operations/MVP_SCOPE.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/operations/MVP_SCOPE.md)
- [docs/operations/OPENCLAW_INTEGRATION.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/operations/OPENCLAW_INTEGRATION.md)
