# Agent Rules

These rules apply to Codex, Claude Code, OpenClaw, or any automation touching the vault.

## Core rules
- Treat the vault as a knowledge system, not just a folder of markdown files.
- Preserve human readability.
- Preserve frontmatter unless intentionally normalizing it.
- Prefer additive changes over destructive changes.
- Never mass-delete notes.
- If archiving is needed, move to `07 - Archives/`.
- If renaming notes, update references when possible.
- Respect the vault folder semantics.

## Change behavior
- prefer small reversible edits
- log important bulk operations
- write clear note titles
- preserve wiki-link friendliness
- do not create noisy duplicate notes
- avoid unnecessary tags explosion

## Review behavior
- create reports for bulk changes
- summarize what was changed
- identify uncertain classifications explicitly
- do not fabricate metadata that should remain unknown

## Documentation behavior
When documenting a project or script:
- optimize for future retrieval
- optimize for future debugging
- optimize for AI reuse
- document why, not only what

## Knowledge behavior
When converting raw information into notes:
- extract durable insights
- keep source attribution inside the note if available
- create concise, reusable note titles
- prefer concept-oriented notes over random fragments
