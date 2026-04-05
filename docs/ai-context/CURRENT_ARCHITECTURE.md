# Current Architecture

## Current logical layers

1. Interface

- Telegram
- OpenClaw
- future surfaces if needed

2. Orchestration

- OpenClaw decides when to converse and when to call tools
- the custom brain-ops plugin exposes the main tool

3. Core

- brain-ops
- routing
- intents
- validation
- deterministic execution
- reports

4. Persistence

- SQLite for operational structured data
- Obsidian for durable memory/documentation/knowledge

5. Local AI

- Ollama for structured parsing and more semantic tasks

## Current repo shape

- src/brain_ops/
- src/brain_ops/services/
- src/brain_ops/ai/
- src/brain_ops/storage/
- src/brain_ops/intents.py
- src/brain_ops/models.py
- src/brain_ops/cli.py
- config/
- docs/
- .openclaw/
- tests/
- data/

## Existing services examples

- handle_input_service.py
- intent_parser_service.py
- intent_execution_service.py
- nutrition_service.py
- diet_service.py
- expenses_service.py
- fitness_service.py
- follow_up_service.py

## Important current separation

- Obsidian = durable knowledge, documentation, summaries, maps
- SQLite = logs and structured day-to-day data
- OpenClaw = conversation and orchestration
- brain-ops = real operational brain
- Ollama = parser and semantic assistant
