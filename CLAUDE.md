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

## Direct knowledge operations (no API needed)

When the user asks Claude Code to work on knowledge directly, Claude should act as the LLM itself — no need to call external APIs. This saves cost and is faster.

Commands the user can give directly:

- **"enriquece [entidad] con [URL]"** — Fetch URL, read current entity note, integrate new info following the enrichment rules (Identity never empty, Key Facts, Timeline, Relationships with [[wikilinks]], Strategic Insights), write updated note to Obsidian.
- **"crea entidad [nombre] tipo [type]"** — Create entity note with proper frontmatter (object_kind, subtype, status:canonical) and subtype-specific sections, in `02 - Knowledge/`.
- **"ingesta [URL]"** — Fetch URL, classify source type, extract structured knowledge (facts, timeline, entities, relationships, insights, contradictions), create source note in `01 - Sources/`.
- **"pregunta: [question]"** — Search vault notes, read relevant ones, synthesize answer with [[wikilinks]] to entities.

Rules for direct operations:
- Use the entity schemas from `src/brain_ops/domains/knowledge/object_model.py` for sections.
- Use canonical predicates from `object_model.py` for relationships.
- Always use [[wikilinks]] for entities mentioned.
- Write in the same language as the entity name (Spanish names → Spanish content).
- Never leave Identity section empty.
- Follow the evidence policy: tag source confidence based on source type.
- **Cross-enrichment**: After writing/enriching any entity, check if the new content contains facts, relationships, or insights about OTHER existing entities. If so, update those related entity notes too. Only add high-confidence, non-redundant facts. Mark cross-enriched items with *(cross-enriched from [[Source Entity]])*.
- Always update frontmatter `related` field with all entities mentioned.
- Always run `brain compile-knowledge` after changes.
- **Source notes**: When enriching from a URL, also create a source note in `01 - Sources/` with the URL, source_type, confidence, and which entity was enriched. Format: `{Entity Name} - {Source Domain}.md`
- **Query learning**: When answering questions, the system logs queries and detects knowledge gaps automatically. Entities mentioned in answers get importance boost in the registry.

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
