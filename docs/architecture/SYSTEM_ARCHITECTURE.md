# System Architecture

## Core architecture

```text
Obsidian Vault (Markdown knowledge layer)
        ^
        |
   brain-ops CLI / services
        ^
        |
  OpenClaw / Claude Code / Codex / scripts
        ^
        |
     Mac mini (execution node)
```

## Layers

### 1. Knowledge layer
A local Obsidian vault containing human-readable notes.

### 2. Operations layer
`brain-ops` manipulates notes and creates structure:
- create notes from templates
- process inbox items
- normalize frontmatter
- classify notes
- generate MOCs
- document scripts
- produce weekly reports
- maintain consistency

### 3. Agent layer
Agents assist with:
- summarization
- classification
- enrichment
- note linking suggestions
- project documentation generation
- repo analysis
- workflow maintenance

### 4. Execution layer
Mac mini runs:
- CLI commands
- background jobs
- Git-protected automations
- OpenClaw workflows
- scheduled maintenance

## Deployment model

### MVP
- local-only
- CLI-first
- path-based vault access
- optional launchd jobs
- no remote API required

### Later
- local private FastAPI service
- Telegram/OpenClaw integration
- dashboards
- event-driven pipelines
- webhook endpoints if needed

## Safety model

All bulk changes should be:
- reviewable
- reversible
- logged
- preferably pre-committed in Git
