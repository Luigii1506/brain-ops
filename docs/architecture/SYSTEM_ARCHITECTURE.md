# System Architecture

## Canonical architecture

```text
User
  |
  v
OpenClaw chat / automations
  |
  v
Ollama local models
  |
  v
brain-ops CLI / services
  |                    |
  v                    v
Obsidian Vault         SQLite
knowledge layer        operational data layer
  |
  v
Git review and rollback
```

## Layer responsibilities

### 1. Interaction layer
OpenClaw receives natural language input and routes it to the right operation.

Examples:
- capture a new concept
- log a meal
- update project documentation
- summarize a workout
- research a note

### 2. Local intelligence layer
Ollama provides local models for:
- interpretation
- rewriting
- extraction
- classification
- summarization

The model layer should remain replaceable and must not own the system state.

### 3. Operations layer
`brain-ops` is the deterministic execution layer.

It should:
- validate input
- choose file/database destinations
- enforce note and folder rules
- write structured markdown
- write structured SQLite rows
- produce reports
- support dry-run where possible

### 4. Knowledge layer
The Obsidian vault stores long-term human-readable artifacts:
- sources
- knowledge
- maps
- systems docs
- project context
- reflections
- summaries and reports

### 5. Structured data layer
SQLite stores operational and quantitative records:
- meals
- meal items
- workouts
- workout sets
- expenses
- body metrics
- daily logs

### 6. Safety layer
Git and reports provide review and rollback for vault-facing changes.

## Data flow

## Knowledge flow
1. User says or writes something.
2. OpenClaw interprets the request.
3. `brain-ops` classifies the request.
4. The system creates or updates a note.
5. The result is visible in Obsidian.

## Life-ops flow
1. User reports a meal, workout, expense, or metric.
2. OpenClaw routes to a structured logging command.
3. `brain-ops` writes rows into SQLite.
4. The system computes summaries and follow-ups.
5. Summary artifacts can be written into the vault when useful.

## Hybrid flow
Some workflows cross both layers.

Examples:
- meal logging updates SQLite and produces a daily nutrition summary note
- project work updates documentation notes and also stores structured activity logs
- repeated operational patterns become durable knowledge or SOPs

## Deployment model

### Laptop
- development and experimentation
- local vault tests
- command testing

### Mac mini
- canonical always-on node
- OpenClaw runtime
- Ollama runtime
- scheduled jobs
- canonical local database
- primary vault automation host

## System boundaries

### Obsidian is for
- memory
- navigation
- documentation
- reflection
- summaries

### SQLite is for
- precise data capture
- repeatable analytics
- quantitative tracking
- high-frequency logs

### AI is for
- interpretation
- assistance
- drafting
- enrichment

### brain-ops is for
- rules
- execution
- structure
- safety

## Near-term implementation modules

- `config`
- `vault`
- `frontmatter`
- `templates`
- `services/`
- `storage/db.py`
- later: `domains/nutrition`, `domains/fitness`, `domains/expenses`

## Safety expectations

- never store secrets in the vault
- prefer additive and reversible changes
- log bulk modifications
- distinguish facts from inferred content
- keep AI writes constrained by deterministic rules
