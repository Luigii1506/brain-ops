# Master Migration Blueprint

## 1. Executive Summary

### What the repository is today

Today this repository is a working local-first operational system with a strong conversation entrypoint, but a much broader underlying purpose than a single assistant or app.

Based on `docs/ai-context/PROJECT_OVERVIEW.md`, `docs/ai-context/CURRENT_ARCHITECTURE.md`, and `docs/ai-context/CURRENT_FLOWS.md`, it currently consists of:

- `brain-ops` as the operational core
- OpenClaw as the orchestration/interface layer
- Telegram as the main user-facing surface
- SQLite as the structured operational store
- Obsidian as the durable knowledge/documentation layer
- Ollama as an auxiliary local intelligence layer

It already supports real flows for:

- user input to action
- structured life-ops logging
- knowledge capture into Obsidian
- deterministic execution with optional AI assistance
- note enrichment and promotion
- review/audit/report generation

So today it is not just a chat assistant. It is closer to a personal SmartHub with several partially connected capabilities, but the structure still reflects a system whose center of gravity is too close to:

- `handle_input`
- intent parsing
- follow-ups
- conversation-driven entry flows

### What it is evolving into

It is evolving into a reusable personal SmartHub / virtual brain, not just a personal assistant or a collection of unrelated mini-apps.

That future direction is explicit in:

- `docs/ai-context/PROJECT_OVERVIEW.md`
- `docs/ai-context/TARGET_ARCHITECTURE.md`
- `docs/ai-context/ARCHITECTURAL_DECISIONS.md`

The future platform must support:

- personal ops
- knowledge ops
- structured daily logging
- source capture and note enrichment
- monitoring
- alerts
- workflows
- reusable APIs
- future research / AML / market intelligence modules

The important point is that no single feature is "the core feature". The real core is the ability to hold structured operational state, durable knowledge, and future observation/monitoring flows inside one modular system that can be reused from other projects.

### The core architectural shift

The key shift is:

from a conversation-centered assistant
to
a capability-centered SmartHub platform

The architecture must stop being centered on:

- intents
- follow-ups
- Telegram/OpenClaw flows

and become centered on:

- domains
- use cases
- events
- observation/intake flows
- workflows
- storage boundaries
- reusable APIs

That shift is the central requirement in `docs/ai-context/TARGET_ARCHITECTURE.md`.

## 2. Current Architecture Assessment

### What is good today and should be preserved

The current system already has several correct architectural decisions that should be preserved.

### Correct separations already present

From `docs/ai-context/CURRENT_ARCHITECTURE.md`:

- Obsidian = durable knowledge, documentation, summaries, maps
- SQLite = structured operational data
- OpenClaw = conversation and orchestration
- brain-ops = operational core
- Ollama = parser / semantic auxiliary

This separation is good and must remain.

### Existing functional layering

The current logical layers are already recognizable:

1. interface
2. orchestration
3. core
4. persistence
5. local AI

That is a good base for incremental migration.

### Existing domain-relevant services

The repo already has domain-oriented services, which is good raw material for refactor:

- `nutrition_service.py`
- `diet_service.py`
- `expenses_service.py`
- `fitness_service.py`

These should not be discarded; they should be migrated into clearer domain modules and cleaner storage-facing adapters.

### What is too conversation-centered

The repository still appears too centered around conversation-driven execution in these areas:

- `handle_input_service.py`
- `intent_parser_service.py`
- `intent_execution_service.py`
- `follow_up_service.py`

This follows directly from `docs/ai-context/CURRENT_FLOWS.md`, which describes the primary flow as:

- Telegram/OpenClaw receives input
- handle_input_service processes it
- intent parser resolves intent
- intent execution triggers domain logic
- follow-up service handles missing info

That means the system’s practical center is still too close to the chat entrypoint.

### Structural risks if the repo keeps growing as-is

If the repo continues to grow around the current structure, the main risks are:

#### 1. Business logic will remain hidden behind conversation flows

This would make the future API, monitoring, automation, and non-chat execution paths harder to build.

#### 2. `intent_execution_service.py` becomes an accidental central dispatcher

That is structurally risky because it makes `intent` the permanent organizing concept instead of `capability` or `use case`.

#### 3. OpenClaw/Telegram concerns may leak into core logic

This would violate:

- `docs/ai-context/NON_NEGOTIABLES.md`
- `docs/ai-context/MIGRATION_RULES.md`

#### 4. Obsidian and SQLite boundaries may blur

If the repo keeps growing through convenience rather than structure, knowledge/documentation and operational state could mix in unsafe ways.

#### 5. Monitoring / automation / future modules will be bolted on awkwardly

The target architecture already expects:

- monitoring
- snapshots
- diffs
- alerts
- workflows
- playbooks
- reusable APIs

If the repo stays organized around chat intent handling, those future modules will have no stable architectural place.

#### 6. The repository will continue to feel like separate apps instead of one system

If nutrition, notes, research, life-ops, and future observation capabilities do not converge on shared architectural boundaries, the project will keep looking like several useful tools that happen to live together instead of one modular SmartHub.

## 3. Target Architecture Blueprint

### Recommended target structure for this repository

This is the recommended target direction, grounded in `docs/ai-context/TARGET_ARCHITECTURE.md`, but adapted safely for incremental migration:

```text
src/brain_ops/
  interfaces/
    telegram/
    openclaw/
    cli/
    api/

  core/
    config/
    logging/
    validation/
    execution/
    events/
    scheduling/
    alerts/
    search/

  domains/
    personal/
      nutrition/
      fitness/
      expenses/
      habits/
      tasks/
      journal/
    knowledge/
      notes/
      summaries/
      research/
      linking/
    monitoring/
      sources/
      monitors/
      snapshots/
      diffs/
      alerts/
    automation/
      workflows/
      playbooks/
      runs/
    projects/
      registry/
      contexts/

  storage/
    sqlite/
    obsidian/
    files/

  ai/
    ollama/
    parsing/
    extraction/
    summarization/
    classification/
```

### Role of each top-level area

### `interfaces/`

What belongs here:

- Telegram-specific input/output adapter code
- OpenClaw integration code
- CLI entry adapters
- future API transport adapters

What must not belong here:

- domain rules
- persistent business workflows
- knowledge ontology rules
- nutrition or expense logic
- SQLite/Obsidian business decisions

### `core/`

What belongs here:

- cross-cutting operational capabilities:
  - config
  - logging
  - validation
  - execution
  - events
  - scheduling
  - alerts
  - search

What must not belong here:

- nutrition rules
- expense rules
- note-specific ontology
- monitoring logic specific to a domain
- chat-specific follow-up logic

Important caution:
`core/` must not become a junk drawer. It should contain only truly shared capabilities.

Additional caution:
Do not introduce `core/routing/` yet unless it is strictly defined as internal use-case dispatch rather than renamed chat-routing logic.

Events caution:
`core/events/` should not be expanded just because the long-term architecture mentions events. It should only grow once there is a repeated pattern of observation/intake/change-processing behavior across multiple services.

### `domains/`

What belongs here:

- business logic by domain
- domain-level use cases
- domain models
- domain-specific rules

Examples:

- nutrition calculations
- diet progress logic
- habit completion logic
- note/summary/research rules
- monitoring snapshot semantics
- workflow logic

What must not belong here:

- Telegram/OpenClaw adapter code
- transport concerns
- direct framework/plugin coupling
- raw storage implementation details

### `storage/`

What belongs here:

- SQLite adapters
- Obsidian adapters
- file-based repositories/adapters

What must not belong here:

- domain rules
- conversation logic
- orchestration policy

Also important:
Obsidian belongs here as technology/infrastructure, not as a domain name.

### `ai/`

What belongs here:

- Ollama integration
- parsing
- extraction
- summarization
- classification

What must not belong here:

- hard-required business operations
- anything that makes critical operations fail if Ollama is down

### `automation/`

Per the target docs, automation is a first-class direction, but the cleanest implementation for this repo is to keep the business meaning in `domains/automation/` and use `core/scheduling/` for shared scheduling primitives.

If a top-level `automation/` directory is used later, it should contain:

- runtime orchestration helpers
- automation configuration
- scheduling glue

What must not happen:
automation should not become a hidden second core.

### `docs/`

What belongs here:

- architecture truth
- migration truth
- ADRs
- operational runbooks
- AI context files
- integration contracts

What must not belong here:

- implementation logic
- hidden source-of-truth rules that are not reflected in code structure over time

## 4. Capability Model

These are the reusable platform capabilities that should become first-class building blocks.

### Config

Purpose:

- runtime configuration
- environment and path resolution
- feature flags

Target module:

- `src/brain_ops/core/config/`

### Validation

Purpose:

- validate input contracts
- validate safe execution
- centralize reusable checks

Target module:

- `src/brain_ops/core/validation/`

### Execution

Purpose:

- standardize use-case execution
- coordinate outcomes/results
- keep interfaces thin

Target module:

- `src/brain_ops/core/execution/`

### Events

Purpose:

- internal event contracts
- decouple action from side effects
- enable monitoring, summaries, alerts, workflows

Target module:

- `src/brain_ops/core/events/`

### Scheduling

Purpose:

- reusable scheduling abstractions
- bridge cron and internal jobs
- support future runs/reviews/reminders

Target module:

- `src/brain_ops/core/scheduling/`

### Alerts

Purpose:

- alert rules
- alert dispatch
- future thresholds/notifications

Target module:

- `src/brain_ops/core/alerts/`

### Search

Purpose:

- reusable search capability across knowledge, monitoring, projects

Target module:

- `src/brain_ops/core/search/`

### Workflows

Purpose:

- reusable multi-step flows
- playbooks
- controlled automation runs

Target module:

- `src/brain_ops/domains/automation/workflows/`
- `src/brain_ops/domains/automation/playbooks/`
- `src/brain_ops/domains/automation/runs/`

### Storage boundaries

Purpose:

- explicit separation of SQLite / Obsidian / files
- keep persistence behind adapters

Target module:

- `src/brain_ops/storage/sqlite/`
- `src/brain_ops/storage/obsidian/`
- `src/brain_ops/storage/files/`

### Summaries

Purpose:

- transform operational state into human-usable summaries
- bridge SQLite and Obsidian

Target module:

- `src/brain_ops/domains/knowledge/summaries/`

### Snapshots / diffs

Purpose:

- future monitoring baseline
- change detection
- research/AML/market intelligence support

Target module:

- `src/brain_ops/domains/monitoring/snapshots/`
- `src/brain_ops/domains/monitoring/diffs/`

### Reusable APIs

Purpose:

- future third-party/backend exposure
- stable capability access beyond chat/CLI

Target module:

- `src/brain_ops/interfaces/api/`

## 5. Domain Model Direction

### Main domain areas

Per `docs/ai-context/TARGET_ARCHITECTURE.md`, the repository should converge toward these main areas:

### `domains/personal/`

Contains:

- nutrition
- fitness
- expenses
- habits
- tasks
- journal

Current services that should evolve here:

- `nutrition_service.py` -> `domains/personal/nutrition/`
- `diet_service.py` -> `domains/personal/nutrition/`
- `fitness_service.py` -> `domains/personal/fitness/`
- `expenses_service.py` -> `domains/personal/expenses/`
- habit-related logic -> `domains/personal/habits/`
- daily log logic -> `domains/personal/journal/`

### `domains/knowledge/`

Contains:

- notes
- summaries
- research
- linking

Current services that should evolve here:

- note capture
- improve note
- research note
- linking
- promote/enrich/summaries

Important correction:
do not create `domains/knowledge/obsidian/` as the main home of knowledge.
Knowledge is the domain.
Obsidian is infrastructure and belongs in `storage/obsidian/`.

### `domains/monitoring/`

Contains:

- sources
- monitors
- snapshots
- diffs
- alerts

This is mostly future-facing, but the structure should be reserved conceptually now because the docs explicitly name monitoring as a core future direction.

### `domains/automation/`

Contains:

- workflows
- playbooks
- runs

This is where reusable operational sequences should live, instead of chat-driven orchestration being the long-term center.

### `domains/projects/`

Contains:

- registry
- contexts

This is the right place for future reusable project context management.

## 6. Dependency and Boundary Rules

These rules are implied by:

- `docs/ai-context/TARGET_ARCHITECTURE.md`
- `docs/ai-context/NON_NEGOTIABLES.md`
- `docs/ai-context/MIGRATION_RULES.md`

### Interface adapters

Examples:

- Telegram
- OpenClaw
- CLI
- future API

May depend on:

- use-case orchestration
- core execution/routing
- DTO/result models

Must not define:

- business rules
- persistent domain behavior
- storage policy

### Application / use-case orchestration

This is the coordination layer between interfaces and domain logic.

May depend on:

- domain modules
- core execution
- core validation
- events
- storage adapters

Must not depend on:

- Telegram-specific assumptions
- OpenClaw-specific prompt flows

### Domain logic

May depend on:

- domain models
- core validation
- core events
- storage abstractions/interfaces

Must not depend on:

- Telegram
- OpenClaw
- Obsidian implementation details
- Ollama availability

### Persistence / infrastructure

Includes:

- SQLite
- Obsidian
- files

May depend on:

- low-level libraries
- config
- infrastructure models

Must not contain:

- domain decisions
- conversation behavior

### AI auxiliary layer

Includes:

- Ollama
- parsing
- extraction
- summarization
- classification

May depend on:

- config
- schemas
- domain input/output contracts

Must not become:

- required execution layer for critical operations

### How to avoid coupling domain logic to Telegram/OpenClaw/Obsidian/Ollama

- do not let domain methods accept Telegram/OpenClaw objects
- do not let domain behavior depend on chat phrasing
- do not encode Obsidian path logic as the meaning of the domain
- do not make Ollama required for correctness
- keep adapters at the edges, not the center

## 7. Resilience and Independence Rules

These follow directly from `docs/ai-context/NON_NEGOTIABLES.md`.

### If OpenClaw is unavailable

Must still work:

- CLI
- core execution
- domain logic
- SQLite operations
- Obsidian operations where available
- cron-driven workflows not dependent on OpenClaw

### If Telegram is unavailable

Must still work:

- OpenClaw via other surfaces if needed
- CLI
- future API
- scheduled jobs
- core and storage layers

### If Obsidian sync fails

Must still work:

- SQLite-backed personal ops
- logging
- validations
- deterministic operations
- summaries may defer or fail gracefully
- knowledge/documentation writes may be retried later

### If Ollama is unavailable

Must still work:

- critical deterministic operations
- structured logging
- direct CLI/API use cases
- safe routing where deterministic fallback exists

Should degrade:

- parsing quality
- extraction
- semantic enrichment
- summarization quality

### If only CLI/API/cron remain available

The system should still be operationally valid.

That means:

- use cases remain callable
- scheduled jobs remain meaningful
- data capture and querying continue
- domain logic remains usable without conversation surfaces

That is a direct architectural requirement of the repository.

## 8. Migration Strategy

The safest migration is incremental and adapter-friendly.

### Phase 1A: Create explicit interface destinations first

Objective:
Make the architecture visibly stop centering around conversation by creating explicit interface adapter destinations early.

Likely affected:

- `src/brain_ops/`

Expected outcome:
The repo gains explicit adapter-layer destinations.
Current CLI/OpenClaw concerns can start being treated as interface concerns rather than core concerns.

Risks:

- creating structure with no immediate behavior movement

Why first:
This directly reframes part of the current conversation-centered structure before larger extraction work.

### Phase 1B: Create the first reusable core destinations

Objective:
Create the minimum reusable core destinations needed for immediate next-step extraction.

Create now:

- `core/execution/`
- `core/validation/`
- `core/events/`
- `domains/personal/`
- `domains/knowledge/`
- `storage/sqlite/`
- `storage/obsidian/`

Expected outcome:
There are now real homes for execution, validation, minimal events, domain extraction, and storage separation.

Risks:

- introducing empty structure without near-term use

Why here:
These are the first destinations that will be used immediately in the next refactor steps.

### Phase 2: Introduce minimal events early

Objective:
Add the smallest useful events capability early enough to support future summaries, alerts, and workflows.

Likely affected:

- selected current life-ops and knowledge flows
- new `core/events/`

Expected outcome:
The system gets a small internal event mechanism without overbuilding.

Risks:

- overengineering events too early

Why now:
The architecture documents make events central to the long-term design, and the smallest useful version already has value.

First event targets:

- `meal_logged`
- `expense_logged`
- `habit_checked`
- `body_metrics_logged`
- `note_captured`
- `summary_generated`
- `diet_activated`

### Phase 3: Extract execution from intent-centered flow

Objective:
Make execution reusable outside chat-driven intents.

Likely affected:

- `src/brain_ops/services/intent_execution_service.py`
- new `src/brain_ops/core/execution/`

Expected outcome:
`intent_execution_service.py` becomes an adapter to reusable execution/use-case functions instead of the central execution brain.

Risks:

- breaking current `handle_input` behavior if done too aggressively

Why here:
Because execution is the most important capability to decouple from conversation flow.

### Phase 4: Extract validation into shared capability

Objective:
Move reusable validation out of scattered parsing/services.

Likely affected:

- parsing-related services
- domain services
- new `core/validation/`

Expected outcome:
shared validation primitives become reusable from CLI, API, cron, Telegram, OpenClaw.

Risks:

- accidental behavior changes in current parsing

Why here:
Because validation is a cross-cutting capability needed before broader API/workflow reuse and future backend exposure.

Validation extraction note:

- `daily_summary_service.py` now uses shared `resolve_iso_date()`
- behavior is unchanged for valid or missing dates
- invalid dates now raise `ConfigError("Date must be in YYYY-MM-DD format.")` instead of a raw `ValueError`
- this change was accepted for consistency

### Phase 5: Split domain logic from service bucket

Objective:
Move real business logic into `domains/personal/*` and `domains/knowledge/*`.

Likely affected:

- `nutrition_service.py`
- `diet_service.py`
- `expenses_service.py`
- `fitness_service.py`
- note/research/linking services

Expected outcome:
domain modules become visible and reusable.

Risks:

- service import churn
- hidden coupling emerging during extraction

Why here:
Because once execution and validation have cleaner homes, domain extraction becomes safer and less ambiguous.

### Phase 6: Move storage concerns behind adapters

Objective:
Separate SQLite and Obsidian logic more clearly from domain logic.

Likely affected:

- `src/brain_ops/storage/db.py`
- vault/obsidian-related file operations
- new `storage/sqlite/`
- new `storage/obsidian/`

Expected outcome:
storage boundaries become explicit and future PostgreSQL/API migration becomes safer.

Risks:

- hidden assumptions in current storage code

Why here:
Because storage extraction is easier once domain boundaries are clearer.

### Phase 7: Reframe conversation as adapter logic more explicitly

Objective:
Reduce structural centrality of:

- `handle_input`
- `intent_parser`
- `follow_up`

Likely affected:

- `handle_input_service.py`
- `intent_parser_service.py`
- `follow_up_service.py`
- `interfaces/openclaw/`

Expected outcome:
conversation becomes one adapter, not the center of the platform.

Risks:

- current Telegram/OpenClaw behavior regressions

Why here:
This becomes safer after reusable execution, validation, initial events, and initial domain extraction exist.

### Phase 8: Prepare monitoring and automation modules

Objective:
Create first real skeleton for:

- monitoring
- workflows
- runs
- alerts

Likely affected:

- new `domains/monitoring/`
- new `domains/automation/`
- `core/alerts/`
- `core/scheduling/`

Expected outcome:
future modules have legitimate architecture destinations.

Risks:

- creating unused complexity too early

Why last:
Because these are future-facing and should build on a stabilized reusable core.

## 9. First 5 Concrete Refactor Tasks

### Task 1: Create the first migration destination folders actually needed for the next step

Goal:
Create only the initial architecture destinations that will be used immediately in the next refactor step.

Likely involved:

- `src/brain_ops/interfaces/`
- `src/brain_ops/interfaces/cli/`
- `src/brain_ops/interfaces/openclaw/`
- `src/brain_ops/core/`
- `src/brain_ops/core/execution/`
- `src/brain_ops/core/validation/`
- `src/brain_ops/core/events/`
- `src/brain_ops/storage/`
- `src/brain_ops/storage/sqlite/`
- `src/brain_ops/storage/obsidian/`
- `src/brain_ops/domains/`
- `src/brain_ops/domains/personal/`
- `src/brain_ops/domains/knowledge/`

What should change:

- add only the minimal package structure that will be used in the immediate next refactor
- avoid deep subtrees that will remain empty
- avoid decorative docstrings or placeholder modules unless they help the next step directly

What must remain compatible:

- current imports
- current CLI
- current OpenClaw integration

Why it matters:
It creates safe destinations for incremental movement without filling the repo with speculative structure.

### Task 2: Extract reusable execution primitives from `intent_execution_service.py`

Goal:
Stop using intent execution as the long-term execution center.

Likely involved:

- current: `src/brain_ops/services/intent_execution_service.py`
- new: `src/brain_ops/core/execution/`

What should change:

- move reusable execution orchestration into core execution
- leave `intent_execution_service.py` as adapter/wrapper

What must remain compatible:

- `handle_input`
- existing commands
- current OpenClaw tool path

Why it matters:
This is the structural pivot away from conversation-centered architecture.

### Task 3: Extract shared validation primitives

Goal:
Create reusable validation outside parser-specific logic.

Likely involved:

- parser services
- life-ops services
- new `src/brain_ops/core/validation/`

What should change:

- move cross-cutting validations into shared modules
- keep current service behavior intact

What must remain compatible:

- current parsing behavior
- current domain commands
- existing CLI contracts

Why it matters:
Validation is needed by future CLI/API/cron reuse.

### Task 4: Start domain extraction for personal ops

Goal:
Make personal ops a real domain structure.

Likely involved:

- `nutrition_service.py`
- `diet_service.py`
- `expenses_service.py`
- `fitness_service.py`
- new `src/brain_ops/domains/personal/...`

What should change:

- move or wrap domain logic into domain modules
- keep old service files as compatibility adapters initially

What must remain compatible:

- current commands
- current database behavior
- current OpenClaw flows

Why it matters:
Personal ops is already real functionality and the safest first domain to extract.

### Task 5: Separate Obsidian as storage adapter, not knowledge domain

Goal:
Avoid coupling knowledge domain to Obsidian implementation.

Likely involved:

- vault/Obsidian-related modules
- new `src/brain_ops/storage/obsidian/`
- new `src/brain_ops/domains/knowledge/notes/`
- new `src/brain_ops/domains/knowledge/summaries/`
- new `src/brain_ops/domains/knowledge/research/`

What should change:

- move technical Obsidian access to storage
- keep knowledge logic in domain modules

What must remain compatible:

- current note capture/improve/research behavior
- existing vault paths and output

Why it matters:
This preserves a clean domain/infrastructure boundary early.

## 10. Anti-Patterns to Avoid

These are repository-specific anti-patterns.

### 1. Keeping `handle_input` as the hidden center of the platform

That would preserve a conversation-first architecture under new folder names.

### 2. Letting `intent_execution_service.py` remain the real execution core

That would keep the system organized around intents instead of reusable capabilities.

### 3. Moving business logic into `core/`

`core/` should not absorb nutrition, expense, knowledge, or monitoring logic.

### 4. Treating `routing/` as renamed conversation parsing

If `core/routing/` is just chat flow logic moved elsewhere, the migration has failed architecturally.

### 5. Putting Obsidian inside the knowledge domain as if it were the domain

Obsidian is infrastructure here, not the domain itself.

### 6. Creating full target architecture folders with no migration value

This would produce architecture theater instead of safe evolution.

### 7. Coupling future monitoring/alerts/workflows to Telegram/OpenClaw

Those must be capabilities of the platform, not chat tricks.

### 8. Making Ollama required for correctness

This would violate resilience rules.

### 9. Moving structured operational state into Obsidian for convenience

This explicitly violates repository non-goals and storage boundaries.

### 10. Rewriting instead of wrapping and migrating

This directly violates `docs/ai-context/MIGRATION_RULES.md`.

## 11. Decision Log Suggestions

These should become ADRs or permanent docs after plan approval.

### ADR 1

`brain-ops` is the operational core; OpenClaw and Telegram are adapters.

### ADR 2

Obsidian is durable knowledge/documentation storage; SQLite is the operational structured store.

### ADR 3

Conversation is an interface, not the center of the platform.

### ADR 4

Execution is being extracted from intent-centered services into reusable core execution.

### ADR 5

Knowledge domain is separate from Obsidian infrastructure.

### ADR 6

Ollama is auxiliary intelligence and must not be a hard dependency for critical operations.

### ADR 7

Events are the future internal mechanism for summaries, alerts, workflows, and monitoring.

### ADR 8

Migration will proceed incrementally via new module destinations + compatibility adapters, not a rewrite.

### ADR 9

The repo is targeting future API/backend reuse and must preserve layer boundaries now.

### ADR 10

Monitoring, automation, and alerting are first-class future modules and must not be bolted on through chat-specific flows.

## 12. Recommended Next Action

The single best next step is:

Create the first minimal destination structure that will be used immediately:

- `interfaces/cli/`
- `interfaces/openclaw/`
- `core/execution/`
- `core/validation/`
- `core/events/`
- `domains/personal/`
- `domains/knowledge/`
- `storage/sqlite/`
- `storage/obsidian/`

and then extract reusable execution primitives out of `intent_execution_service.py` into `core/execution/`, while keeping the current services as compatibility adapters.

Why this first:

- it does not rewrite the system
- it preserves current behavior
- it starts the real architectural shift
- it breaks the strongest current conversation-centered dependency
- it prepares all later domain and storage migrations

## Proposed Repository Skeleton (Incremental Version)

This is the realistic intermediate structure to create first, before the full target architecture:

```text
src/brain_ops/
  interfaces/
    cli/
    openclaw/

  core/
    execution/
    validation/
    events/

  domains/
    personal/
    knowledge/

  storage/
    sqlite/
    obsidian/

  ai/
    # no new subtree required in the first step
```

Why this intermediate version first:

- it is small enough to be safe
- it gives the current repo real migration destinations
- it avoids empty architectural theater
- it supports the next refactors immediately
- it keeps compatibility while moving the center away from chat flow and toward reusable capabilities
