# Agent Rules

These rules apply to Codex, Claude Code, OpenClaw, or any automation touching the system.

## Core rules

- Treat the vault as a knowledge system, not as a generic file dump.
- Treat SQLite as the source of truth for structured operational logs.
- Preserve human readability in Markdown outputs.
- Prefer additive changes over destructive changes.
- Never mass-delete notes.
- Respect the vault ontology and folder semantics.
- Do not collapse quantitative tracking into random markdown notes if structured storage is better.

## Change behavior

- prefer small reversible edits
- log important bulk operations
- avoid noisy duplicate notes
- preserve wiki-link friendliness
- avoid tags explosion
- keep deterministic logic around AI-generated content

## Review behavior

- create reports for bulk changes
- summarize what was changed
- identify uncertain classifications explicitly
- distinguish found facts from inferred content

## Documentation behavior

When documenting projects, systems, or commands:
- optimize for future retrieval
- optimize for future debugging
- optimize for AI reuse
- document why, not only what

## Knowledge behavior

When converting raw information into notes:
- extract durable insights
- keep source attribution inside the note if available
- prefer concept-oriented notes over random fragments
- do not confuse placeholders with mature knowledge

## Life-ops behavior

When handling meals, workouts, expenses, or metrics:
- store precise entries in SQLite
- write summaries and reflections to Obsidian only when useful
- preserve units and timestamps
- avoid inventing numeric values
