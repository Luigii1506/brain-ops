# brain-ops OpenClaw Plugin

This is the workspace-native OpenClaw plugin scaffold for `brain-ops`.

## Purpose

It exposes `brain-ops` as OpenClaw tools so the final interaction path can be:

```text
Telegram -> OpenClaw -> brain-ops -> Obsidian + SQLite
```

## Current status

This is a first scaffold.

It is intended for the Mac mini environment where OpenClaw is actually installed and running.
It has not been runtime-tested in this laptop workspace because OpenClaw is not installed here.

## Files

- `openclaw.plugin.json`
  Native plugin manifest with minimal config schema

- `index.ts`
  Native plugin entry that registers the first `brain-ops` tools

## Initial tool set

- `brain_ops_handle_input`
- `brain_ops_route_input`
- `brain_ops_daily_summary`
- `brain_ops_daily_macros`
- `brain_ops_spending_summary`

## Expected plugin config

Suggested config under `plugins.entries.brain-ops.config`:

```json
{
  "brainCommand": "brain",
  "workingDirectory": "/path/to/brain-ops",
  "configPath": "/path/to/brain-ops/config/vault.yaml"
}
```

## Workspace loading

OpenClaw can discover workspace extensions from:

- `<workspace>/.openclaw/extensions/*/index.ts`

This plugin lives at:

- `.openclaw/extensions/brain-ops`

## Notes

- `brain-ops` remains the source of truth for routing and execution.
- OpenClaw should stay thin and call these tools instead of reimplementing logic.
- Telegram remains just the user-facing channel.
