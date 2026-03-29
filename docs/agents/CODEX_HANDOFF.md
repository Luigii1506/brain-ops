# Codex Handoff

This repository supports a local-first Jarvis-style system, not just a markdown notes utility.

## Core system roles

- Obsidian = human-facing memory, navigation, and documentation layer
- SQLite = structured operational tracking layer
- brain-ops = deterministic operations and transformation layer
- OpenClaw = conversational orchestration layer
- Ollama = local model runtime
- Mac mini = primary always-on node
- Git = safety boundary for vault-facing changes

## What Codex should optimize for

- reliable note operations
- explicit ontology and folder semantics
- local structured storage for life-ops domains
- commands that OpenClaw can call safely
- minimal manual maintenance for the user
- local-first execution

## Main jobs to support

- create, normalize, improve, enrich, and promote notes
- maintain project documentation
- maintain systems documentation and commands
- initialize and later query SQLite
- support future nutrition, fitness, and expense commands
- preserve clear boundaries between knowledge artifacts and structured logs

## Constraints

- local-first
- markdown-first for knowledge
- SQLite-first for quantitative tracking
- no secrets in vault
- reversible changes preferred
- avoid overengineering

## Recommended implementation style

- Python-first
- CLI-first
- modular
- deterministic around side effects
- explicit config
- human-readable outputs
- safe defaults

## First read on the Mac mini

If Codex is running on the Mac mini and needs environment context, read these first:
- [docs/setup/MAC_MINI_SETUP.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/setup/MAC_MINI_SETUP.md)
- [docs/MASTER_PLAN.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/MASTER_PLAN.md)
- [docs/operations/OPENCLAW_INTEGRATION.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/operations/OPENCLAW_INTEGRATION.md)

Do not assume:
- the vault path
- the config path
- the installed Ollama model
- the OpenClaw plugin state

Verify those first on the target machine.

## Commands that matter most now

- `brain info`
- `brain init`
- `brain init-db`
- `brain audit-vault`
- `brain normalize-frontmatter`
- `brain capture`
- `brain improve-note`
- `brain research-note`
- `brain apply-link-suggestions`
- `brain promote-note`
- `brain enrich-note`
- `brain process-inbox`

## What should come next

- SQLite-backed domain modules
- OpenClaw routing conventions
- Mac mini deployment setup
- life-ops summaries into the vault
