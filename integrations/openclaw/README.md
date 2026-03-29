# OpenClaw Integration Assets

This folder contains the project-owned integration assets for OpenClaw.

## Purpose

These files exist so OpenClaw can use `brain-ops` as its deterministic backend.

The intended interaction channel is:

```text
Telegram -> OpenClaw -> brain-ops -> Obsidian + SQLite
```

## Files

- `manifest.json`
  Preferred tool manifest for OpenClaw integrations.

## Rules

- OpenClaw is the conversational/orchestration layer.
- `brain-ops` remains the execution layer.
- Telegram is only the chat channel; it must not bypass OpenClaw.
- Obsidian and SQLite remain the system of record.
