# Mac Mini Setup

## Purpose

This document is the canonical bootstrap guide for the production Mac mini.

Use it when:
- setting up the machine for the first time,
- reconnecting with Codex on the Mac mini,
- validating that the Jarvis stack is actually ready,
- or recovering the environment after changes.

This setup is for the real runtime path:

```text
Telegram -> OpenClaw -> brain-ops -> Obsidian Vault + SQLite
                         |
                         v
                       Ollama
```

## Target state

By the end of this setup, the Mac mini should have:
- the `brain-ops` repo cloned locally
- the Obsidian vault available locally
- Python environment ready
- `brain` CLI runnable
- SQLite database initialized
- Ollama installed and running
- the production local model installed
- OpenClaw installed and gateway running
- the workspace OpenClaw plugin scaffold discoverable
- config pointing to the real vault and data paths

## Read This First

Before doing anything on the Mac mini, read:
- [README.md](/Users/luisencinas/Documents/GitHub/brain-ops/README.md)
- [docs/MASTER_PLAN.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/MASTER_PLAN.md)
- [docs/architecture/SYSTEM_ARCHITECTURE.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/architecture/SYSTEM_ARCHITECTURE.md)
- [docs/operations/OPENCLAW_INTEGRATION.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/operations/OPENCLAW_INTEGRATION.md)
- [docs/agents/CODEX_HANDOFF.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/agents/CODEX_HANDOFF.md)

## Assumptions

- macOS
- user has admin access
- Obsidian vault will exist locally on the Mac mini
- Telegram will be the user-facing chat channel
- OpenClaw will be the orchestration layer
- Ollama will be the local model runtime
- `brain-ops` will be the deterministic backend

## 1. Clone the repository

```bash
cd ~/Documents/GitHub
git clone <repo-url> brain-ops
cd brain-ops
```

If the repo already exists:

```bash
cd ~/Documents/GitHub/brain-ops
git pull --ff-only
```

## 2. Prepare Python

Verify Python:

```bash
python3 --version
```

Create a virtual environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install project dependencies according to the repo standard in use.
If packaging is already configured, prefer the project-native install path.

At minimum, verify the CLI imports:

```bash
PYTHONPATH=src python -m brain_ops.cli --help
```

## 3. Place the Obsidian vault locally

The Mac mini must have a local copy of the vault.

Do not point `brain-ops` at a remote-only location.

Confirm the real local path, for example:

```bash
ls ~/Documents
```

Expected vault structure should include:
- `00 - Inbox`
- `01 - Sources`
- `02 - Knowledge`
- `03 - Maps`
- `04 - Projects`
- `05 - Systems`
- `06 - Daily`
- `07 - Archive`

## 4. Create the Mac mini config

Copy the example config:

```bash
cp config/vault.example.yaml config/vault.macmini.yaml
```

Then edit it with the real Mac mini paths.

Required fields to verify:
- `vault_path`
- `data_dir`
- `database_path`
- `ollama_host`
- `orchestrator`
- `primary_model`
- `reasoning_model`
- `parser_model`
- `enable_llm_routing`

Recommended production values:
- `ai_provider: "ollama"`
- `orchestrator: "openclaw"`
- `enable_llm_routing: true`
- `primary_model: "qwen3.5:9b"`
- `reasoning_model: "qwen3.5:9b"`
- `parser_model: "qwen3.5:9b"`

Use explicit model tags.
Do not use `latest` in production.

## 5. Initialize the local database

Run:

```bash
PYTHONPATH=src python -m brain_ops.cli init-db --config config/vault.macmini.yaml
```

Validate:

```bash
PYTHONPATH=src python -m brain_ops.cli info --config config/vault.macmini.yaml
```

## 6. Install and start Ollama

Install Ollama on the Mac mini following the official instructions.

Then verify the daemon:

```bash
curl -s http://127.0.0.1:11434/api/tags
```

Install the intended production model:

```bash
ollama pull qwen3.5:9b
```

Validate:

```bash
ollama run qwen3.5:9b
```

Then update `config/vault.macmini.yaml` to match that exact tag.

## 7. Validate brain-ops with Ollama

Run:

```bash
PYTHONPATH=src python -m brain_ops.cli route-input "Tomé 5g de creatina" --use-llm --json --config config/vault.macmini.yaml
PYTHONPATH=src python -m brain_ops.cli handle-input "Gasté 120 en Oxxo y aprendí algo sobre idempotencia" --use-llm --json --dry-run --config config/vault.macmini.yaml
```

What to confirm:
- valid JSON output
- `routing_source` is present
- multi-action still works
- no broken fallback path

## 8. Install and start OpenClaw

Install OpenClaw using the official method for the Mac mini.

Then onboard:

```bash
openclaw onboard --install-daemon
```

Check gateway status:

```bash
openclaw gateway status
```

Open the dashboard if useful:

```bash
openclaw dashboard
```

## 9. Enable the workspace plugin scaffold

This repo includes a native workspace plugin scaffold at:

- `.openclaw/extensions/brain-ops`

OpenClaw can discover workspace extensions from:
- `<workspace>/.openclaw/extensions/*/index.ts`

The plugin files are:
- [.openclaw/extensions/brain-ops/openclaw.plugin.json](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/openclaw.plugin.json)
- [.openclaw/extensions/brain-ops/index.ts](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/index.ts)
- [.openclaw/extensions/brain-ops/README.md](/Users/luisencinas/Documents/GitHub/brain-ops/.openclaw/extensions/brain-ops/README.md)

If needed, also add the repo path explicitly in OpenClaw config using `plugins.load.paths`.

Then:

```bash
openclaw plugins list
openclaw plugins inspect brain-ops --json
openclaw plugins enable brain-ops
openclaw gateway restart
```

Plugin config should point at:
- the `brain` executable
- the repo working directory
- the Mac mini config path

Expected conceptual config:

```json
{
  "plugins": {
    "entries": {
      "brain-ops": {
        "enabled": true,
        "config": {
          "brainCommand": "brain",
          "workingDirectory": "/Users/YOUR_USER/Documents/GitHub/brain-ops",
          "configPath": "/Users/YOUR_USER/Documents/GitHub/brain-ops/config/vault.macmini.yaml"
        }
      }
    }
  }
}
```

## 10. Export the OpenClaw manifest

Regenerate the manifest from the CLI:

```bash
PYTHONPATH=src python -m brain_ops.cli openclaw-manifest --output integrations/openclaw/manifest.json --no-json
```

This keeps the OpenClaw tool contract aligned with the repo state.

## 11. Telegram channel integration

Telegram is not the backend.
Telegram is the user-facing channel.

The intended path is:
- user sends message in Telegram
- OpenClaw receives the message
- OpenClaw calls `brain-ops`
- `brain-ops` writes to vault or SQLite

So when validating Telegram, you are really validating:
- Telegram channel works
- OpenClaw receives it
- OpenClaw tool calling works
- `brain-ops` returns structured JSON

## 12. Smoke tests

Run these after setup:

```bash
PYTHONPATH=src python -m brain_ops.cli info --config config/vault.macmini.yaml
PYTHONPATH=src python -m brain_ops.cli audit-vault --config config/vault.macmini.yaml
PYTHONPATH=src python -m brain_ops.cli handle-input "Desayuné yogurt con avena y platano y tomé 5g de creatina" --dry-run --json --config config/vault.macmini.yaml
PYTHONPATH=src python -m brain_ops.cli daily-summary --date 2026-03-29 --json --config config/vault.macmini.yaml
```

If OpenClaw is active, also validate:
- plugin appears in `openclaw plugins list`
- plugin can be enabled
- OpenClaw can call the `brain-ops` tool path without shell issues

## 13. What not to do on the Mac mini

- do not store secrets in the vault
- do not use `latest` model tags in production
- do not let Telegram bypass OpenClaw
- do not let OpenClaw write directly to the vault or SQLite
- do not reimplement routing outside `brain-ops`

## 14. If Codex lands on the Mac mini without context

Start by reading, in this order:
1. [docs/setup/MAC_MINI_SETUP.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/setup/MAC_MINI_SETUP.md)
2. [docs/MASTER_PLAN.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/MASTER_PLAN.md)
3. [docs/operations/OPENCLAW_INTEGRATION.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/operations/OPENCLAW_INTEGRATION.md)
4. [docs/agents/CODEX_HANDOFF.md](/Users/luisencinas/Documents/GitHub/brain-ops/docs/agents/CODEX_HANDOFF.md)

Then verify:
- repo path
- vault path
- config path
- database path
- Ollama model installed
- OpenClaw plugin discovery

Only after that should implementation continue.
