# Action Plan — brain-ops Next Phase

## Where We Are

### Migration progress (Blueprint Phases 1-7): COMPLETE

The architectural migration from conversation-centered to capability-centered is done:
- Destination structure created (interfaces/, core/, domains/, storage/)
- Events system with JSONL event log and emission across all commands
- Execution extracted from intent-centered flow into application/ layer
- Shared validation in core/validation/
- Domain extraction complete for personal and knowledge
- Storage adapters for SQLite (11 modules) and Obsidian (10 modules)
- Conversation reframed as adapter (45 files in interfaces/conversation/)

### Phase 8 (Monitoring & Automation): ~60%

What exists:
- Event log monitoring with summary, tail, report, hotspots, failures
- Alert evaluation with configurable policies (lenient/default/strict presets)
- Alert messaging and delivery pipeline (file/stdout, json/text, archive/latest/both)
- Delivery presets (default, file-text, stdout-json, stdout-text, archive-only)

What's missing:
- External source monitoring (scraping, API observation)
- Automation workflows, playbooks, runs
- Scheduling primitives (core/scheduling/)

### What exists per domain today

| Domain | Location | Content |
|--------|----------|---------|
| Personal | `domains/personal/` | diet, fitness, nutrition, goals, tracking, daily_status — SOLID |
| Knowledge | `domains/knowledge/` | Note operations: capture, link, improve, research, audit, promote, enrich — SOLID but no entity model |
| Projects | `domains/knowledge/projects.py` | Only scaffold generation — MINIMAL, should be its own domain |
| Monitoring | `application/monitoring.py` | Event log only — no external source monitoring |
| Automation | `application/automation.py` | Alert delivery only — no general workflows |

---

## Where We Need To Go

### The three core domains must align with the user's vision

1. **Personal** — Luis's daily life (diet, exercise, expenses, habits, journal, reading list, pending tasks)
2. **Projects** — His dev work (docs, commands, state, AI context per project)
3. **Knowledge** — His encyclopedia (historical figures, events, geography, science, books, authors)

### Cross-cutting capabilities must become real

- **Monitoring/scraping**: observe websites and APIs daily via cron
- **API layer**: expose data for React/Next.js frontends
- **Automation**: compile pipeline (raw → wiki), lint, health checks
- **Knowledge compile**: Obsidian frontmatter → SQLite for app consumption

---

## Action Plan — Ordered by Value and Safety

### Block A: Knowledge Entity Model (HIGH VALUE — enables the encyclopedia)

**Why first**: This is the core of the "second brain" vision. Without typed entities, knowledge is just loose notes. With them, Luis gets his personal Wikipedia with cross-references, relationships, and future quiz/learning apps.

**A1. Define entity types and frontmatter schema**

Create `domains/knowledge/entities.py` with:
- Entity type registry: `person`, `event`, `place`, `concept`, `book`, `country`, `war`, `era`, `author`, `topic`
- Frontmatter schema per type (what fields each entity type has)
- Validation: given a note's frontmatter, is it a valid entity of type X?
- Relationship extraction: parse `related` field from frontmatter

Example frontmatter for a person:
```yaml
---
type: person
name: Alejandro Magno
born: 356 BC
died: 323 BC
nationality: Macedonia
era: Antigüedad
related:
  - Aristóteles
  - Batalla de Gaugamela
  - Darío III
  - Imperio Persa
tags: [history, military, conqueror]
---
```

Example for an event:
```yaml
---
type: event
name: Batalla de Gaugamela
date: 331 BC
location: Gaugamela, Mesopotamia
participants:
  - Alejandro Magno
  - Darío III
related:
  - Imperio Persa
  - Macedonia
  - Guerras de Alejandro
tags: [history, battle, ancient]
---
```

**A2. Entity creation workflow**

Add to `application/knowledge.py`:
- `execute_create_entity_workflow()` — creates a typed entity note in Obsidian with proper frontmatter and template body
- Uses Ollama optionally to generate initial content from entity name + type

CLI command: `brain-ops create-entity "Alejandro Magno" --type person`

**A3. Entity index generation**

Add to `domains/knowledge/`:
- `index.py` — scans vault for entity notes, generates INDEX.md grouped by type
- Auto-maintained: re-run on ingest or via cron

CLI command: `brain-ops knowledge-index`

**A4. Entity relationship graph**

Add to `domains/knowledge/`:
- `relations.py` — extract relationships from frontmatter `related` fields
- Build adjacency map: given entity X, what entities are connected?
- Use for future query answering and navigation

CLI command: `brain-ops entity-relations "Alejandro Magno"`

### Block B: Projects Domain Separation (HIGH VALUE — solves AI context loss)

**Why now**: Luis manages ~6 projects and loses context every new AI conversation. This is a daily pain point.

**B1. Create `domains/projects/` as independent domain**

Move `domains/knowledge/projects.py` scaffolding logic to `domains/projects/scaffold.py`.

Add:
- `domains/projects/registry.py` — project metadata: name, path, status, tech stack, description
- `domains/projects/context.py` — project state: current phase, recent decisions, what's pending, key commands

**B2. Project registration and context workflows**

Add to `application/projects.py`:
- `execute_register_project_workflow()` — registers a project with metadata
- `execute_update_project_context_workflow()` — updates current state, decisions, pending items
- `execute_project_context_workflow()` — retrieves full context for a project

CLI commands:
- `brain-ops register-project "brain-ops" --path ~/Documents/GitHub/brain-ops --stack python,typer,sqlite`
- `brain-ops project-context "brain-ops"` — shows full current context
- `brain-ops update-project-context "brain-ops" --phase "Phase 8 automation" --pending "monitoring domain"`

**B3. Auto-generate CLAUDE.md per project**

Add to `application/projects.py`:
- `execute_generate_claude_md_workflow()` — generates a CLAUDE.md from project context + recent state
- Writes to the project's repo directory

CLI command: `brain-ops generate-claude-md "brain-ops"`

Storage: project registry in SQLite (structured, queryable), context notes in Obsidian (human-readable).

### Block C: Monitoring / Scraping Domain (HIGH VALUE — enables observing the world)

**Why now**: This connects to Karpathy's ingest pattern and is a core brain-ops capability.

**C1. Create `domains/monitoring/` with source model**

- `domains/monitoring/sources.py` — source definition: URL, type (web/api), check frequency, selectors/paths to watch
- `domains/monitoring/snapshots.py` — capture current state of a source
- `domains/monitoring/diffs.py` — compare two snapshots, detect changes

**C2. Scraper execution workflow**

Add to `application/monitoring.py`:
- `execute_check_source_workflow()` — fetch source, create snapshot, diff against previous, generate events
- `execute_check_all_sources_workflow()` — run all registered sources

CLI commands:
- `brain-ops add-source "https://example.com/page" --type web --selector ".content"`
- `brain-ops check-source "example-page"`
- `brain-ops check-all-sources`

**C3. Change → Knowledge pipeline**

When a diff is detected:
- Alert via existing alerting stack
- Optionally auto-create/update a note in Obsidian with the change summary
- Log event in event system

Storage: source registry and snapshots in SQLite, change summaries in Obsidian.

### Block D: Knowledge Compile Pipeline (MEDIUM VALUE — enables apps)

**Why**: Bridges Obsidian (source of truth) → SQLite (queryable for APIs/apps).

**D1. Frontmatter extraction and compile**

- `domains/knowledge/compile.py` — scan vault for entity notes, extract frontmatter, write structured data to SQLite
- Tables: `entities`, `entity_relations`, `entity_metadata`

CLI command: `brain-ops compile-knowledge`

**D2. Knowledge query API preparation**

- Once compiled to SQLite, the future API layer can serve:
  - `GET /entities?type=person` → all persons
  - `GET /entities/alejandro-magno` → entity with relations
  - `GET /entities/alejandro-magno/relations` → connected entities

This block is prep work for the API layer but doesn't require the API itself yet.

### Block E: Automation & Scheduling (MEDIUM VALUE — enables cron workflows)

**E1. Scheduling primitives**

- `core/scheduling/` — cron job definitions, run tracking
- Bridge between brain-ops workflows and system cron

**E2. Automated workflows**

Connect existing pieces into automated flows:
- Daily: `check-all-sources` → alerts on changes
- Weekly: `audit-vault` → `knowledge-index` → health report
- On ingest: `capture` → `improve` → `link-suggestions` → `apply-links`

### Block F: API Layer (FUTURE — after data model is solid)

**F1. Create `interfaces/api/`**

- FastAPI or similar lightweight framework
- Expose personal data (habits, diet, expenses) for frontend apps
- Expose knowledge entities for quiz/learning apps
- Expose project context for AI tools

**F2. Frontend consumption**

React/Vite/Next.js apps that consume the API:
- Habit tracker dashboard
- Diet/macro viewer
- Quiz app from knowledge entities
- Project dashboard

---

## Execution Order Recommendation

```
Block A (Knowledge Entities) ─── most foundational, enables the encyclopedia
  ↓
Block B (Projects Domain) ─── solves daily pain point, independent of A
  ↓
Block C (Monitoring/Scraping) ─── enables observing the world
  ↓
Block D (Knowledge Compile) ─── bridges Obsidian → SQLite for apps
  ↓
Block E (Automation/Scheduling) ─── connects everything with cron
  ↓
Block F (API Layer) ─── exposes everything for frontends
```

Blocks A and B can be worked in parallel since they're independent.
Block C can start after A since monitoring feeds into knowledge.
Blocks D, E, F build on top of A+B+C.

---

## Rules (carried from existing migration)

- Follow Codex patterns: application/ → cli/ → tests → exports → migration status
- Obsidian as source of truth for knowledge, SQLite for structured/queryable data
- No rewrites — wrap and migrate incrementally
- Frontmatter is the bridge between human-readable and machine-queryable
- Every new capability gets: application workflow → CLI command → tests → exports
- LLM (Ollama) is always optional — critical operations must work without it
