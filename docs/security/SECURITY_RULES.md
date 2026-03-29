# Security Rules

## Absolute rules

- Never store real passwords in the Obsidian vault.
- Never store production secrets or API keys in the vault.
- Never commit secrets to Git.
- Never expose private notes through a public API.
- Never let an agent perform destructive bulk edits without review protections.

## Approved patterns

Use the vault to store:
- secret references
- setup instructions
- usage context
- links to secret managers
- rotation procedures

Use dedicated secret stores for actual secrets:
- 1Password
- Bitwarden
- macOS Keychain
- environment variables
- secret managers

## Operational protections

Before large vault edits:
- create a Git commit or backup snapshot
- generate a report of intended changes
- prefer dry-run mode where possible

After large vault edits:
- inspect changed files
- validate backlinks if notes were renamed
- confirm vault still renders correctly in Obsidian
