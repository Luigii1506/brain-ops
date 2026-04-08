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

**BEFORE writing — quality check (CRITICAL):**
1. WebFetch the source URL to get the full content
2. Identify ALL major sections/topics in the source
3. Ask yourself: "If someone reads only my note, will they understand this entity completely?"
4. For important entities (historical figures, empires, battles): every major event, campaign, relationship, and turning point MUST be represented — not just mentioned, but explained
5. Don't write from general knowledge alone — verify against the source

**Checklist for important entities (person, empire, battle, civilization):**
- Are ALL major campaigns/events covered? (not just the famous ones)
- Are key turning points explained? (not just listed as dates)
- Are important relationships described with context? (not just "father of")
- Are strategic decisions and their consequences included?
- Are contradictions and uncertainties noted?
- Would a reader understand WHY this entity matters, not just WHAT happened?

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

**For long sources (Wikipedia, long articles):** Use multi-pass to avoid truncation:
```bash
brain multi-enrich "Entity Name" --url "https://..." --llm-provider openai --config config/vault.yaml
```
This downloads the full source, saves it as raw, splits into chunks, and runs multiple enrich passes so nothing is lost.

**Raw source persistence:** Post-process with `--source-url` automatically downloads and saves the full raw source to `.brain-ops/raw/`. This enables future re-processing and audit.

**What Claude CANNOT do when writing directly (only the pipeline does these):**
- Save extraction JSON (no LLM extraction happened)
- Emit events to event log
- Update entity_registry.json automatically (must be done manually or via reconcile)
- Normalize predicates programmatically
- Trigger auto-entity creation

### Signals — never mix these:
- `source_count` = evidence from ingested sources (only API pipeline increments this)
- `query_count` = user interest from questions asked (only query-knowledge increments this)
- `relation_count` = graph connections
- `gap_count` = entities missing from query answers

Vault path: `/Users/luisencinas/Documents/Obsidian Vault`
Config: `config/vault.yaml`

## Preferred implementation stack

- Python
- Typer
- Pydantic
- pathlib
- YAML/frontmatter helpers
- sqlite3
- Rich for CLI output
