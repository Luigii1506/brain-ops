# Codex Task Prompt

Use this repository as the operations layer for a local-first Obsidian-based second brain.

## Objective
Build `brain-ops` as a professional Python CLI toolkit that can safely automate and maintain an Obsidian vault.

## Required characteristics
- local-first
- modular
- markdown-aware
- filesystem-safe
- Git-friendly
- agent-friendly
- easy to extend

## First implementation priorities
1. central configuration
2. vault path validation
3. frontmatter read/write support
4. note creation from templates
5. inbox processing primitives
6. project scaffolding
7. report generation
8. dry-run support for bulk operations

## Non-goals for the first version
- public API
- GUI
- database
- heavy plugin system
- cloud deployment

## Coding expectations
- use Python
- organize code into focused modules
- write docstrings
- keep side effects explicit
- provide clear CLI messages
- prefer pathlib
- avoid hidden magic

## Safety expectations
- do not destroy data
- provide dry-run mode
- archive instead of deleting
- preserve human readability
