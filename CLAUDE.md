# CLAUDE.md

This repository powers a local-first personal operating system built around:
- an Obsidian vault for knowledge and documentation,
- SQLite for structured life-ops data,
- OpenClaw and Ollama for local AI workflows.

## Repository intent

The user wants one system that can:
- capture and organize knowledge,
- maintain project and technical documentation,
- track diet, gym, expenses, and daily operational data,
- run locally on a Mac mini,
- stay structured, auditable, and extensible.

## Behavioral rules

- Never store secrets in the vault.
- Never treat all data as markdown if it should be structured.
- Prefer small, reversible edits.
- For bulk vault changes, generate a report.
- Preserve compatibility with Obsidian.
- Keep Markdown human-readable.
- Keep SQLite as the source of truth for quantitative tracking domains.
- Avoid fake metadata and fake facts.

## Priority tasks

1. Keep the knowledge ops core reliable.
2. Preserve the vault ontology.
3. Add local structured storage for life-ops domains.
4. Keep the project ready for OpenClaw + Ollama.
5. Favor deterministic execution around AI behavior.

## Knowledge operations — workflow rules

Claude Code acts as both LLM and system operator. The key rule is:

**ALWAYS prefer official commands over direct file editing.**

See also: `docs/operations/AGENT_DIRECT_LLM_WORKFLOWS.md` for reusable direct-agent prompt templates and command-equivalence workflows.

### Priority order for every operation:

1. **USE OFFICIAL COMMAND** if one exists (`brain create-entity`, `brain enrich-entity`, etc.)
2. **Write directly + run post-processing** only if no command exists for the task
3. **NEVER just edit a note and walk away** — always run reconciliation after direct edits

### When using official commands (preferred):

```bash
# Create entity (uses correct frontmatter, subtype sections, compiles)
brain create-entity "Name" --type person --config config/vault.yaml

# Enrich from URL (uses source strategy, chunking, extraction, cross-enrichment)
brain enrich-entity "Name" --url "https://..." --llm-provider openai --config config/vault.yaml

# Ingest source (creates source note + updates registry + saves extraction JSON)
brain ingest-source --url "https://..." --use-llm --config config/vault.yaml

# Query WITHOUT LLM (logs query, detects gaps, updates query_count — $0)
brain query-knowledge "question" --config config/vault.yaml

# Query WITH LLM (same + synthesized answer — costs API)
brain query-knowledge "question" --llm-provider openai --config config/vault.yaml

# Post-process after Claude writes directly (emit event, source note, extraction log, registry, compile)
brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml

# Reconcile all direct edits at once (registry sync + compile only)
brain reconcile --config config/vault.yaml

# Audit
brain audit-knowledge --config config/vault.yaml

# Suggestions
brain suggest-entities --config config/vault.yaml
```

### When Claude writes directly (as the LLM):

This is allowed when the user says "enriquece X" or "crea entidad X" in conversation.
Claude acts as the LLM directly (no API cost). But MUST follow these rules:

**BEFORE writing — determine mode:**

DEEP MODE (person, empire, civilization, battle, war, country, book, discipline):
1. Run `brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml`
2. Use the generated raw source and pass plan from `.brain-ops/direct-enrich/<slug>.json`
3. Write pass by pass covering ALL high-priority sections and valuable medium ones
4. After writing, run `brain post-process ...` and `brain check-coverage ...`
5. If coverage still shows important gaps, do another direct pass focused on those sections and post-process again

LIGHT MODE (cities, simple concepts, animals, minor entities):
1. WebFetch or use general knowledge
2. Write a solid note covering the essentials
3. No formal coverage check needed

**Rule: "If the source has it AND it's structurally important, the note covers it."**

Not ALL sections — only the important ones. References, bibliography, metadata = skip.
Campaigns, turning points, death, legacy = always cover.

**Checklist for DEEP MODE entities:**
- Are ALL major campaigns/events covered? (not just the famous ones)
- Are key turning points explained? (not just listed as dates)
- Are important relationships described with context?
- Are strategic decisions and their consequences included?
- Are contradictions and uncertainties noted?
- Would a reader understand WHY this entity matters?

**While writing any entity note directly:**
1. Update frontmatter `related` field with all entities mentioned
2. Use subtype-specific sections from `object_model.py`
3. Use canonical predicates from `object_model.py` for relationships
4. Always use [[wikilinks]] for entities mentioned
5. Never leave Identity section empty
6. Write in the same language as the entity name

**After writing, verify coverage:**
```bash
brain post-process "Entity Name" --source-url "https://url-used" --config config/vault.yaml
brain check-coverage "Entity Name" --config config/vault.yaml
```
If check-coverage shows high-priority gaps, enrich those sections before moving on.

**After verification, close the pipeline:**
```bash
brain post-process "Entity Name" --source-url "https://url-used" --config config/vault.yaml
```
This single command does everything: emits event, creates source note, saves extraction record, syncs registry, and compiles to SQLite.

If multiple entities were edited, run `brain reconcile` instead (bulk sync without per-entity traceability).

**For long sources (Wikipedia, long articles) when the agent is the LLM:** Use the direct planning pipeline:
```bash
brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml
```
This downloads the full source, saves it as raw, splits it into multi-pass contexts, ranks useful chunks by subtype, and writes a reusable plan file so Claude/Codex can follow the same deterministic structure without API calls.

**For long sources when you DO want the provider pipeline:** use:
```bash
brain multi-enrich "Entity Name" --url "https://..." --llm-provider openai --config config/vault.yaml
```

**Raw source persistence:** Post-process with `--source-url` automatically downloads and saves the full raw source to `.brain-ops/raw/`. This enables future re-processing and audit.

**Standard no-API direct-enrich workflow for large entities:**
1. `brain create-entity "Entity Name" --type person --config config/vault.yaml` (if the note does not exist)
2. `brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml`
3. Claude/Codex writes the note using the generated pass contexts in order
4. `brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml`
5. `brain check-coverage "Entity Name" --config config/vault.yaml`
6. If needed, do one more focused direct pass and run `post-process` again

**What direct writing ALONE cannot do before post-processing:**
- Persist raw source automatically
- Save the extraction record automatically
- Sync the entity registry automatically
- Compile back to SQLite automatically
- Trigger auto-entity creation

### Signals — never mix these:
- `source_count` = evidence from ingested sources (only API pipeline increments this)
- `query_count` = user interest from questions asked (only query-knowledge increments this)
- `relation_count` = graph connections
- `gap_count` = entities missing from query answers

Vault path: `/Users/luisencinas/Documents/Obsidian Vault`
Config: `config/vault.yaml`

## Project operations — agent workflow rules

**BEFORE starting work:**
1. Run `brain session brain-ops --context-only --config config/vault.yaml`
2. Read the output to understand: current state, next actions, blockers, recent decisions
3. This is your working context — do NOT ask the user to re-explain the project

**AFTER completing significant work:**
1. Log what you did: `brain project-log brain-ops "resumen de lo que hiciste" --config config/vault.yaml`
2. Refresh the project docs/context pack: `brain refresh-project brain-ops --config config/vault.yaml`
3. For decisions, prefix with "decisión:": `brain project-log brain-ops "decisión: usar X por Y" --config config/vault.yaml`
4. For bugs found, prefix with "bug:": `brain project-log brain-ops "bug: descripción" --config config/vault.yaml`
5. For next steps, prefix with "next:": `brain project-log brain-ops "next: lo que sigue" --config config/vault.yaml`

**AFTER git commits:**
The repository now uses shared git hooks:
- `.githooks/post-commit` runs `brain project-log` and `brain refresh-project`
- `.githooks/post-merge` and `.githooks/post-rewrite` run `brain refresh-project`

This keeps the vault project docs and context pack synchronized when the repository changes. Only log manually if the change is architecturally significant beyond the commit itself or if no commit was made.

## Preferred implementation stack

- Python
- Typer
- Pydantic
- pathlib
- YAML/frontmatter helpers
- sqlite3
- Rich for CLI output
