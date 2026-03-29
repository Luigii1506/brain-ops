# Codex Handoff

This repository exists to support a local-first, agent-assisted knowledge operations system around an Obsidian vault.

## What Codex should understand immediately

### Primary purpose
This project is not a generic notes utility.  
It is an automation layer for a personal second brain.

### System roles
- Obsidian = human interface for knowledge
- brain-ops = structured automation layer
- Mac mini = local execution host
- Git = safety boundary
- OpenClaw / Claude Code / Codex = intelligent operators

### Main jobs to support
- create and normalize notes
- process inbox items
- classify notes
- generate MOCs
- document scripts and projects
- maintain consistency
- produce reports
- assist safe automation

## Constraints
- local-first
- markdown-first
- no secrets in vault
- minimal manual friction
- reversible changes preferred
- avoid overengineering the MVP

## Preferred implementation style
- Python-first
- CLI-first
- modular
- testable
- explicit config
- filesystem-based
- human-readable outputs

## Important UX assumptions
The user wants:
- a professional structure
- one place for interconnected project documentation and study
- minimal manual maintenance
- high automation leverage
- compatibility with agent workflows

## Recommended initial commands
- `brain init`
- `brain process-inbox`
- `brain create-project`
- `brain create-note`
- `brain generate-moc`
- `brain document-script`
- `brain normalize-frontmatter`
- `brain weekly-review`

## Deliverables Codex should favor
- clean Python modules
- maintainable CLI commands
- templates
- reports
- safe file operations
- clear error handling
- dry-run support where possible
