# brain-ops

`brain-ops` is the operational backend for a personal "second brain" system built around an Obsidian vault.

The vault is the human-facing layer for thinking, studying, documenting, and navigating knowledge.  
This project is the machine-facing layer for automation, classification, documentation generation, linking, review workflows, and agent orchestration.

## Core purpose

This system should let a single user:

- keep projects, notes, study material, SOPs, and technical documentation in one place,
- automate note creation, classification, enrichment, and maintenance,
- use local and external AI agents safely,
- document repositories, scripts, architectural decisions, and workflows intelligently,
- run on a Mac mini as a 24/7 knowledge and automation node,
- stay local-first, modular, and reversible.

## Design principles

- Local-first
- Markdown-first
- Obsidian-compatible
- Agent-assisted, not agent-chaotic
- Git-protected
- Modular CLI first
- API optional later
- Security-conscious
- Easy to review, audit, and extend

## System boundaries

### What belongs in the Obsidian vault
- project notes
- MOCs
- permanent notes
- source notes
- study notes
- runbooks
- SOPs
- decision logs
- architecture notes
- debugging notes
- reading notes
- prompts and reusable workflows

### What does NOT belong in the vault
- production secrets
- API keys
- raw large datasets
- logs dumps
- virtualenvs
- node_modules
- build artifacts
- binary junk
- temporary machine-only clutter

## Main components

- `src/brain_ops/` — application logic
- `docs/` — product, architecture, and workflow documentation
- `templates/` — note templates used to create consistent Obsidian notes
- `config/` — local config examples and conventions
- `prompts/` — instructions for agents like Codex / Claude Code / OpenClaw

## Recommended environment

- Python project
- runs locally on a Mac mini
- operates against a local Obsidian vault path
- protected by Git
- invoked from CLI
- optionally orchestrated by OpenClaw / launchd / cron

## High-level vision

Obsidian is the human brain interface.  
`brain-ops` is the operations layer that keeps the knowledge system clean, documented, connected, and useful.

Read `docs/PRODUCT_VISION.md` first.
