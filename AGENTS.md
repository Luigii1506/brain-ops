# AGENTS.md — brain-ops

This is the operational context for any AI agent working on this project.

## Before starting ANY task

1. Run this command and read the output:
```bash
brain session brain-ops --context-only --config config/vault.yaml
```
2. This gives you: current state, next actions, blockers, recent decisions, commands
3. Do NOT ask the user to re-explain the project. The context is in the system.

## After completing significant work

Log what you did:
```bash
brain project-log brain-ops "what you did" --config config/vault.yaml
```

Use prefixes for classification:
- `"decisión: usar X por Y"` → saved to Decisions.md + registry
- `"bug: description"` → saved to Debugging.md
- `"next: what comes next"` → saved to registry pending

## After git commits

Commits are auto-logged via hooks. Only run `brain project-log` manually if the change involves an architectural decision or is particularly significant.

## Project overview

**brain-ops** is a personal intelligence station — a local-first operating system combining:
- **Obsidian vault** for knowledge entities and reflective notes
- **SQLite** for structured life-ops data (diet, fitness, expenses, habits)
- **Multi-provider LLM** (Ollama, OpenAI, Claude, DeepSeek, Gemini)
- **CLI-first** interface via Typer + Rich

## Stack

Python, Typer, Pydantic, SQLite, FastAPI (optional), Rich

## Key commands

```bash
# Run tests
python -m pytest tests/ -x -q

# System info
brain info --config config/vault.yaml

# Knowledge operations
brain create-entity "Name" --type person --config config/vault.yaml
brain enrich-entity "Name" --url "..." --llm-provider openai --config config/vault.yaml
brain full-enrich "Name" --url "..." --config config/vault.yaml
brain check-coverage "Name" --config config/vault.yaml
brain reconcile --config config/vault.yaml
brain post-process "Name" --source-url "..." --config config/vault.yaml

# Personal operations
brain capture "natural language text"
brain daily-review --config config/vault.yaml
brain week-review --config config/vault.yaml

# Project operations
brain session brain-ops --config config/vault.yaml
brain project-log brain-ops "update text" --config config/vault.yaml
brain audit-project brain-ops --config config/vault.yaml
```

## Architecture (quick reference)

```
Interfaces (CLI, API, OpenClaw)
    ↓
Application (workflows)
    ↓
Domains (business logic: knowledge, personal, projects, monitoring)
    ↓
Storage (SQLite + Obsidian vault + JSON registries)
```

- **SQLite** = source of truth for operational data (meals, workouts, expenses, project logs)
- **Obsidian** = source of truth for knowledge entities, reflections, project documentation
- **Registry JSON** = lightweight index (entity registry, project registry)
- **Config**: `config/vault.yaml`
- **Vault path**: `/Users/luisencinas/Documents/Obsidian Vault`

## Knowledge operations rules

When creating or enriching entities, follow these rules from CLAUDE.md:
1. Use official commands (`brain create-entity`, `brain enrich-entity`) over direct file editing
2. After direct edits, always run `brain post-process` or `brain reconcile`
3. Never mix signals: `source_count` (evidence) vs `query_count` (interest) vs `relation_count` (structure)
4. Deep mode entities (person, empire, civilization, battle): full coverage check required
5. Always save raw source, use `_index.json` for lookup

## Safety

- Never store secrets in the vault or commit them
- Never run destructive commands without asking
- Prefer small, reversible edits
- Keep tests passing before committing
