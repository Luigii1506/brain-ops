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
- Ollama as the local model runtime
- optional terminal and scheduled jobs

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
- workout sessions
- sets and reps
- expenses
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
- report and audit conventions across both vault and database

## Phase 3: Life-ops modules
Deliver:
- nutrition logging and macro tracking
- workout logging and progression tracking
- expense logging and summaries
- daily operational log
- summary generation into the vault

## Phase 4: Context-aware agent behavior
Deliver:
- OpenClaw tool calling conventions
- domain-aware command selection
- persistent memory strategy
- context packs for projects and personal domains

## Phase 5: Continuous operation on Mac mini
Deliver:
- launchd jobs
- nightly reviews
- automated report generation
- sync-safe workflows
- resilient local deployment

## Immediate next milestones

1. Stabilize the docs around the real architecture.
2. Keep building the knowledge ops core.
3. Add the first SQLite-backed life-ops commands.
4. Integrate OpenClaw on the Mac mini.
5. Use Obsidian as the review and navigation layer, not the only storage layer.

## Success criteria

The system is successful if the user can:
- talk to it naturally,
- capture knowledge without friction,
- keep technical documentation current,
- log meals, workouts, and expenses conversationally,
- retrieve context later from Obsidian,
- and trust that the system remains local, structured, and reviewable.
