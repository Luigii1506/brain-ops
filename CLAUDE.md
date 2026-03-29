# CLAUDE.md

This repository powers a local-first second-brain operations toolkit for an Obsidian vault.

## Repository intent
The user wants a professional system that:
- documents projects intelligently
- processes and organizes notes
- generates structured documentation
- supports AI-assisted workflows
- runs well on a local Mac mini node
- keeps everything interconnected and reviewable

## Behavioral rules
- Never store secrets in notes.
- Never add fake metadata.
- Prefer small, reversible edits.
- For bulk edits, generate a report.
- Favor human-readable Markdown.
- Preserve compatibility with Obsidian.
- Treat templates and note structure as first-class design concerns.
- Avoid overengineering the MVP.

## Priority tasks
1. Build a reliable CLI foundation.
2. Add vault-aware file operations.
3. Support frontmatter normalization.
4. Support note templates.
5. Support project scaffolding.
6. Support inbox processing.
7. Support reporting.
8. Later consider a private local API if justified.

## Preferred implementation stack
- Python
- Typer
- Pydantic
- pathlib
- YAML/frontmatter helpers
- Rich for CLI output
