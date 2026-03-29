# Master Plan

## System thesis

`brain-ops` is being built as a local-first personal operating system.

The target outcome is not "better note-taking".
The target outcome is a Jarvis-like system that can:
- capture and structure knowledge,
- maintain project and technical documentation,
- track personal operational data,
- answer from local context,
- and help the user run life and work from one coherent system.

## Final architecture

### 1. Interaction layer
- OpenClaw as the main conversational and orchestration interface
- Telegram as the primary user-facing chat channel into OpenClaw
- Ollama as the local model runtime
- optional terminal and scheduled jobs
- a routing layer that can classify and execute safe local actions before heavier orchestration

### 2. Execution layer
- `brain-ops` as the deterministic engine
- command routing
- validation
- note creation and transformation
- reporting
- safe file operations
- data writes into SQLite

### 3. Knowledge layer
- Obsidian vault as the long-term memory system
- Markdown notes for durable knowledge, project context, systems docs, maps, reflections, and reports

### 4. Structured data layer
- SQLite for operational logs and quantitative tracking
- nutrition
- fitness
- expenses
- body metrics
- daily structured events

### 5. Safety layer
- Git for review and rollback
- dry-run where possible
- reports for bulk actions
- no secret storage in the vault

## Domain model

### Knowledge domains
- world knowledge
- technical knowledge
- personal reflections
- project context
- operational procedures
- source material

### Life-ops domains
- nutrition
- fitness
- expenses
- habits
- daily logs
- body metrics

## Storage rules

### Goes to Obsidian
- durable concepts
- facts worth remembering
- reflections
- source notes
- maps of content
- project notes
- architecture and debugging notes
- commands, SOPs, runbooks
- summaries derived from quantitative logs

### Goes to SQLite first
- meals
- food items
- macro totals
- supplements
- workout sessions
- sets and reps
- expenses
- habit check-ins
- metric snapshots
- structured daily events

### Goes to both
- daily or weekly summaries
- project status snapshots
- insights extracted from repeated data
- coaching-style feedback

## Operating modes

### 1. Capture
Input from chat, CLI, voice transcript, URL, PDF, or repo path.

System decides whether to:
- create a note
- update a note
- log structured data
- ask for clarification later through workflow rules

### 2. Improve
Existing notes get clearer structure and better readability.

### 3. Research
Notes are enriched with grounded external information and attribution.

### 4. Link
The system suggests and applies useful internal links.

### 5. Promote
The system turns sources into durable knowledge and stubs into draft notes.

### 6. Track
The system logs meals, workouts, expenses, and daily metrics in structured storage.

### 7. Review
The system produces summaries, audits, and follow-up actions.

## Implementation phases

## Phase 1: Knowledge ops foundation
Status: in progress

Deliver:
- vault config
- safe file operations
- templates
- capture
- normalize frontmatter
- improve note
- research note
- link suggestions
- apply links
- promote note
- enrich note
- inbox processing
- audit and weekly review

## Phase 2: Local Jarvis infrastructure
Deliver:
- AI config for OpenClaw + Ollama
- SQLite initialization
- domain tables
- command routing conventions
- heuristic pre-routing before model orchestration
- report and audit conventions across both vault and database

## Phase 3: Life-ops modules
Deliver:
- nutrition logging and macro tracking
- supplement logging
- workout logging and progression tracking
- expense logging and summaries
- habit tracking
- daily operational log
- summary generation into the vault

## Phase 4: Context-aware agent behavior
Deliver:
- OpenClaw tool calling conventions
- Telegram -> OpenClaw -> brain-ops interaction flow
- domain-aware command selection
- persistent memory strategy
- context packs for projects and personal domains

## Phase 5: Continuous operation on Mac mini
Deliver:
- documented bootstrap and recovery runbook
- launchd jobs
- nightly reviews
- automated report generation
- sync-safe workflows
- resilient local deployment

## Current implemented baseline

### Knowledge ops
- capture
- improve-note
- research-note
- promote-note
- enrich-note
- process-inbox
- normalize-frontmatter
- audit-vault
- weekly-review
- link-suggestions
- apply-link-suggestions

### Structured life-ops
- log-meal
- daily-macros
- log-supplement
- habit-checkin
- daily-habits
- log-body-metrics
- body-metrics-status
- log-workout
- workout-status
- log-expense
- spending-summary
- daily-log
- daily-summary

### Input handling
- route-input
- handle-input
- heuristic extraction for meals, supplements, habits, workouts, expenses, and basic knowledge capture
- JSON output mode for route-input and handle-input
- routing source markers for heuristic, llm, and hybrid decisions
- multi-action execution for mixed safe inputs
- OpenClaw integration manifest and contract docs

## Master backlog

This section is the living source of truth for pending work.

Rule:
- when a pending item is completed, move it out of `Now` or `Next`
- when a new important pending item appears, add it here
- do not rely on chat memory alone; this document is the persistent plan

## Now

### 1. Strengthen natural-language extraction
Improve parsing for:
- meals without rigid formatting
- expenses with merchants/categories mixed into text
- supplements with units and variants
- habits with negation or partial completion
- distinction between reflections and workouts
- more robust mixed-intent splitting when users send long combined messages

Why now:
- this is the shortest path to a more Jarvis-like interaction style

### 2. Mac mini Ollama rollout
Keep local-model rollout pending for the Mac mini environment:
- download and pin `qwen3.5:9b`
- update config defaults and examples to the chosen production model
- validate `handle-input --use-llm` performance on the Mac mini
- only then promote that model to the default local parser/runtime

Why now:
- Ollama works on the laptop, but this is not the target machine and we do not want to download large models here

### Future integrations
Keep these as optional integrations after the core is stable:
- OpenClaw plugin/skill owned by this project as the preferred integration path
- ClawHub skills only as optional complements, never as the system core
- `qmd` as a possible markdown search enhancer
- Office-to-Markdown style ingestion for documents and study material
- external research tooling only when it improves grounded research without replacing `brain-ops`
- Obsidian-specific tooling only if it adds UI convenience; the source of truth remains the vault plus SQLite

Rule:
- do not let third-party skills redefine the architecture
- evaluate them as adapters around `brain-ops`, not replacements for it

## Next

### 3. Ollama-assisted parsing layer hardening
Strengthen the current local model-assisted parsing layer:
- rules first
- Ollama when ambiguity is medium/high
- deterministic validation before execution
- stricter JSON/schema enforcement
- better fallback and latency handling
- richer extracted fields for OpenClaw consumption

Use cases:
- mixed-intent input
- informal or long descriptions
- deciding create vs update note
- extracting richer fields from natural language

### 4. Goals and targets
Add local configurable targets for:
- macro goals
- workout goals
- budget targets
- habit goals

This unlocks:
- "what do I still need today?"
- "am I over budget?"
- "did I hit my workout target this week?"

## Later

### 5. Query layer
Support higher-level questions like:
- how many macros do I have left today
- what supplements have I taken this week
- how much did I spend on food this month
- how many workouts did I do this week
- what habits am I missing most often

### 6. Automatic note updates and summaries
Generate or update:
- daily notes
- weekly summaries
- health summaries
- spending summaries
- project status snapshots

### 7. Better knowledge decisions
Improve:
- update existing note vs create new note
- source-to-knowledge promotion triggers
- MOC generation and maintenance
- smarter linking and de-duplication

## Eventually

### 8. OpenClaw full integration on Mac mini
Integrate:
- OpenClaw as the main interface
- Ollama as the default local model runtime
- tool execution against `brain-ops`
- Mac mini as the canonical always-on node

### 9. Background automation
Add:
- launchd jobs
- nightly/weekly jobs
- summary generation
- vault/database maintenance workflows

### 10. Persistent context and project memory
Build:
- context packs
- domain-aware memory retrieval
- stronger personal/project context for future agent decisions

## Important constraints for future work

- keep deterministic execution as the source of truth
- use models to parse and assist, not to own system state
- do not move all life data into markdown
- do not let routing become opaque
- keep Obsidian for memory and SQLite for structured operational data
- keep Git as the review boundary for vault-facing automation

## Success criteria

The system is successful if the user can:
- talk to it naturally,
- capture knowledge without friction,
- keep technical documentation current,
- log meals, workouts, and expenses conversationally,
- retrieve context later from Obsidian,
- and trust that the system remains local, structured, and reviewable.
