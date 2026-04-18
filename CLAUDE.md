# CLAUDE.md

This repository powers a local-first personal operating system built around:
- an Obsidian vault for knowledge and documentation,
- SQLite for structured life-ops data,
- OpenClaw and Ollama for local AI workflows.

## Repository intent

The user wants one system that can:
- capture and organize knowledge,
- maintain project and technical documentation,
- track diet, gym, expenses, and daily operational data,
- run locally on a Mac mini,
- stay structured, auditable, and extensible.

## Behavioral rules

- Never store secrets in the vault.
- Never treat all data as markdown if it should be structured.
- Prefer small, reversible edits.
- For bulk vault changes, generate a report.
- Preserve compatibility with Obsidian.
- Keep Markdown human-readable.
- Keep SQLite as the source of truth for quantitative tracking domains.
- Avoid fake metadata and fake facts.

## Priority tasks

1. Keep the knowledge ops core reliable.
2. Preserve the vault ontology.
3. Add local structured storage for life-ops domains.
4. Keep the project ready for OpenClaw + Ollama.
5. Favor deterministic execution around AI behavior.

## Knowledge operations — workflow rules

Claude Code acts as both LLM and system operator. The key rule is:

**ALWAYS prefer official commands over direct file editing.**

See also: `docs/operations/AGENT_DIRECT_LLM_WORKFLOWS.md` for reusable direct-agent prompt templates and command-equivalence workflows.

### Priority order for every operation:

1. **USE OFFICIAL COMMAND** if one exists (`brain create-entity`, `brain enrich-entity`, etc.)
2. **Write directly + run post-processing** only if no command exists for the task
3. **NEVER just edit a note and walk away** — always run reconciliation after direct edits

### When using official commands (preferred):

```bash
# Create entity (uses correct frontmatter, subtype sections, compiles)
brain create-entity "Name" --type person --config config/vault.yaml

# Enrich from URL (uses source strategy, chunking, extraction, cross-enrichment)
brain enrich-entity "Name" --url "https://..." --llm-provider openai --config config/vault.yaml

# Ingest source (creates source note + updates registry + saves extraction JSON)
brain ingest-source --url "https://..." --use-llm --config config/vault.yaml

# Query WITHOUT LLM (logs query, detects gaps, updates query_count — $0)
brain query-knowledge "question" --config config/vault.yaml

# Query WITH LLM (same + synthesized answer — costs API)
brain query-knowledge "question" --llm-provider openai --config config/vault.yaml

# Post-process after Claude writes directly (emit event, source note, extraction log, registry, compile)
brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml

# Reconcile all direct edits at once (registry sync + compile only)
brain reconcile --config config/vault.yaml

# Audit
brain audit-knowledge --config config/vault.yaml

# Suggestions
brain suggest-entities --config config/vault.yaml

# Schema + naming lint (Campaña 0 — read-only)
brain lint-schemas --config config/vault.yaml
brain lint-schemas --naming --json --config config/vault.yaml
brain lint-schemas --subtype person --config config/vault.yaml

# Schema migrations for knowledge.db (automatic backup)
brain migrate-knowledge-db --status --config config/vault.yaml
brain migrate-knowledge-db --dry-run --config config/vault.yaml
brain migrate-knowledge-db --config config/vault.yaml
# Exceptional: bypass test-runner / env var guards. Still creates backup.
brain migrate-knowledge-db --force-migrate --config config/vault.yaml

# Reconcile with body-safe skip flags (Campaña 1 operations)
brain reconcile --skip-wikify --skip-cross-enrich --config config/vault.yaml
```

### Body-safety rules for bulk operations (Campaña 1)

During bulk consolidation campaigns, the default `brain reconcile` can
introduce semantic errors (e.g. wikify linking `la Ética kantiana` to
`[[Ética (Spinoza)|Ética]]` — the book, not the discipline). To prevent
this, Campaña 1 uses these rules:

- **Frontmatter-only subfases (domain aliases, fill-domain, epistemic_mode,
  subtype re-classification):** post-step is `brain compile-knowledge`.
  Never modifies `.md` bodies.
- **Rename / disambiguation subfases (capitalization fixes, bare-name
  disambiguation):** post-step is `brain reconcile --skip-wikify
  --skip-cross-enrich`. Registry syncs and SQLite compiles without body
  edits.
- **Default `brain reconcile`** (with wikify + cross-enrich) is unsafe
  during Campaña 1 operations. Do not use it until Campaña 1 completes.
- Every bulk `--apply` is preceded by a manual snapshot of `02 - Knowledge`
  at `<vault>/.brain-ops/backups/02-knowledge-pre-<subfase>-<timestamp>`.
- Every `--apply` is followed by a full-tree byte hash check to detect
  unintended body changes.

See `docs/operations/CAMPAIGN_1_OPERATIONS.md`.

### Safety guards (Campaña 0.5)

The production `knowledge.db` is NEVER modified as a side effect of
imports, tests, or workflow execution. Migrations only run when the user
explicitly invokes `brain migrate-knowledge-db`.

- `initialize_entity_tables` only runs idempotent DDL — it does NOT migrate.
- `apply_migrations` is guarded by `BRAIN_OPS_NO_MIGRATE=1` and by
  `sys.modules` detection of test runners.
- `load_validated_vault` refuses to open the user's real vault under
  `BRAIN_OPS_BLOCK_REAL_VAULT=1` or a detected test runner.
- Tests set both env vars via `tests/__init__.py` and `tests/conftest.py`.
- Legacy DBs trigger `SchemaOutOfDateError` with a clear message when a
  write path depends on post-migration columns.

Verification after a test run:

```bash
sha256sum "<vault>/.brain-ops/knowledge.db" > /tmp/db-pre.sha
python -m unittest discover tests
sha256sum "<vault>/.brain-ops/knowledge.db" > /tmp/db-post.sha
diff /tmp/db-pre.sha /tmp/db-post.sha  # must be empty
```

See `docs/operations/MIGRATIONS.md` for the full policy.

### Taxonomy, naming and epistemology (Campaña 0)

- Canonical domain slugs: `historia`, `filosofia`, `ciencia`, `religion`,
  `esoterismo`, `machine_learning`. English / accented variants are accepted
  as aliases and reported by `brain lint-schemas --naming`.
- New subtypes available: `historical_period`, `dynasty`, `historical_process`,
  `organism`, `species`, `language`, `script`, `gene`, `cell`, `chemical_element`,
  `compound`, `molecule`, `disease`, `theorem`, `constant`,
  `mathematical_object`, `mathematical_function`, `mathematical_field`,
  `proof_method`, `sacred_text`, `esoteric_text`, `esoteric_tradition`,
  `occult_movement`, `ritual`, `symbolic_system`, `divination_system`,
  `mystical_concept`.
- New relations: `reacted_against`, `developed`, `extended`, `synthesized`,
  `refuted`, `criticized`, `inspired`, `derived_from`, `belongs_to_period`,
  `contemporary_of`, `emerged_from`, `transformed_into`, `ruled_by`,
  `centered_on`, `continuation_of`, `worshipped`, `worshipped_by`,
  `associated_with`, `symbolizes`, `used_in`, `practiced_by`,
  `interpreted_as`, `appears_in`, `depicts`, `describes`, `argues_for`,
  `argues_against`, `written_in`, `based_on`, `explains`, `measured_by`,
  `studied_in`, `part_of_system`, `precedes_in_process`, `depends_on`,
  `participated_in`.
- Epistemic layer: notes in `ciencia`, `religion`, `filosofia`, `esoterismo`
  should carry `epistemic_mode`. `create-entity` auto-applies sensible defaults.
  See `docs/operations/EPISTEMOLOGY.md`.
- See also: `docs/operations/NAMING_RULES.md`,
  `docs/operations/CAMPAIGN_0_SUMMARY.md`,
  `MASTER_KNOWLEDGE_GRAPH_BLUEPRINT.md`.

### When Claude writes directly (as the LLM):

This is allowed when the user says "enriquece X" or "crea entidad X" in conversation.
Claude acts as the LLM directly (no API cost). But MUST follow these rules:

**BEFORE writing — determine mode:**

DEEP MODE (person, empire, civilization, battle, war, country, book, discipline):
1. Run `brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml`
2. Use the generated raw source and pass plan from `.brain-ops/direct-enrich/<slug>.json`
3. Write pass by pass covering ALL high-priority sections and valuable medium ones
4. After writing, run `brain post-process ...` and `brain check-coverage ...`
5. If coverage still shows important gaps, do another direct pass focused on those sections and post-process again

LIGHT MODE (cities, simple concepts, animals, minor entities):
1. WebFetch or use general knowledge
2. Write a solid note covering the essentials
3. No formal coverage check needed

**Rule: "If the source has it AND it's structurally important, the note covers it."**

Not ALL sections — only the important ones. References, bibliography, metadata = skip.
Campaigns, turning points, death, legacy = always cover.

**Checklist for DEEP MODE entities:**
- Are ALL major campaigns/events covered? (not just the famous ones)
- Are key turning points explained? (not just listed as dates)
- Are important relationships described with context?
- Are strategic decisions and their consequences included?
- Are contradictions and uncertainties noted?
- Would a reader understand WHY this entity matters?

**While writing any entity note directly:**
1. Update frontmatter `related` field with all entities mentioned
2. Use subtype-specific sections from `object_model.py`
3. Use canonical predicates from `object_model.py` for relationships
4. Always use [[wikilinks]] for entities mentioned
5. Never leave Identity section empty
6. Write in the same language as the entity name
7. **ALWAYS include `## Preguntas de recuperación`** with 5 questions:
   - 🟢 Recordar (1): dato concreto, fecha, nombre
   - 🟡 Explicar (2): por qué, cómo, causa-efecto
   - 🔴 Comparar (1): similitud/diferencia con otra entidad
   - ⚫ Aplicar (1): lección, patrón, transferencia
   Format: `- 🟢 **¿Pregunta?** → Respuesta concreta`

8. **For `person` entities, include `## Frases célebres`** if the person has notable quotes.
   Format per quote:
   ```
   > "Texto de la frase."
   > — Contexto: cuándo, dónde, a quién se la dijo
   ^quote-slug-identificador

   tema:: liderazgo, filosofía
   contexto:: breve descripción de la situación
   fecha:: ~336 a.C.
   confiabilidad:: alta | media | baja | apócrifa | tradicional
   fuente:: Plutarco, Vida de Alejandro
   ```
   Rules:
   - `^quote-slug` block ID is mandatory — enables `![[Persona#^quote-slug]]` from thematic MOCs
   - `confiabilidad` is mandatory — many famous quotes are misattributed
   - `tema` enables thematic collection grouping
   - Only include quotes with historical/pedagogical value, not trivia
   - Thematic MOC collections (`Frases - Liderazgo.md`, etc.) live in `03 - Maps/` and use block refs (`![[Persona#^quote-slug]]`), never duplicate the text

**After writing, verify coverage:**
```bash
brain post-process "Entity Name" --source-url "https://url-used" --config config/vault.yaml
brain check-coverage "Entity Name" --config config/vault.yaml
```
If check-coverage shows high-priority gaps, enrich those sections before moving on.

**After verification, close the pipeline:**
```bash
brain post-process "Entity Name" --source-url "https://url-used" --config config/vault.yaml
```
This single command does everything: emits event, creates source note, saves extraction record, syncs registry, and compiles to SQLite.

If multiple entities were edited, run `brain reconcile` instead (bulk sync without per-entity traceability).

### Semantic relationship workflow

Use semantic relationship review when the user asks why cross-enrichment did not create a graph edge, when a new myth/person/concept note mentions important entities in prose, or after adding a cluster of related knowledge notes.

`cross-enrich` is for explicit wikilink cleanup. `semantic-relations` is for contextual graph reasoning:

```bash
# Inspect likely existing relationships and missing entity candidates
brain semantic-relations "Entity Name" --config config/vault.yaml

# Add high-confidence semantic links in the analyzed note
brain semantic-relations "Entity Name" --fix --config config/vault.yaml

# Add the analyzed-note links and reciprocal links in destination notes
brain semantic-relations "Entity Name" --fix --bidirectional --config config/vault.yaml
```

When using `--bidirectional`, act as a domain expert for the entity's subject before accepting the result. Read the analyzed note and the destination notes that will receive backlinks. The relation should make sense from both sides, not only because a name appears in text.

For each accepted relation:
- The source note should explain why the destination matters in its own context.
- The destination note should receive a reciprocal relation only when the source is meaningful to that destination's identity, mythology, argument, or narrative role.
- Prefer contextual predicates and reasons over generic graph edges when editing manually.
- Preserve each note's preferred prose style and language.
- Do not create missing entities automatically from this command; use the "Missing entity candidates" list as a creation queue and create those entities through `brain create-entity` or direct-enrich workflow.

After semantic relation edits, run:

```bash
brain cross-enrich --fix --config config/vault.yaml
brain reconcile --config config/vault.yaml
```

**For long sources (Wikipedia, long articles) when the agent is the LLM:** Use the direct planning pipeline:
```bash
brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml
```
This downloads the full source, saves it as raw, splits it into multi-pass contexts, ranks useful chunks by subtype, and writes a reusable plan file so Claude/Codex can follow the same deterministic structure without API calls.

**For long sources when you DO want the provider pipeline:** use:
```bash
brain multi-enrich "Entity Name" --url "https://..." --llm-provider openai --config config/vault.yaml
```

**Raw source persistence:** Post-process with `--source-url` automatically downloads and saves the full raw source to `.brain-ops/raw/`. This enables future re-processing and audit.

**Standard no-API direct-enrich workflow for large entities:**
1. `brain create-entity "Entity Name" --type person --config config/vault.yaml` (if the note does not exist)
2. `brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml`
3. Claude/Codex writes the note using the generated pass contexts in order
4. `brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml`
5. `brain check-coverage "Entity Name" --config config/vault.yaml`
6. If needed, do one more focused direct pass and run `post-process` again

**What direct writing ALONE cannot do before post-processing:**
- Persist raw source automatically
- Save the extraction record automatically
- Sync the entity registry automatically
- Compile back to SQLite automatically
- Trigger auto-entity creation

### Signals — never mix these:
- `source_count` = evidence from ingested sources (only API pipeline increments this)
- `query_count` = user interest from questions asked (only query-knowledge increments this)
- `relation_count` = graph connections
- `gap_count` = entities missing from query answers

Vault path: `/Users/luisencinas/Documents/Obsidian Vault`
Config: `config/vault.yaml`

## Project operations — agent workflow rules

**BEFORE starting work:**
1. Run `brain session brain-ops --context-only --config config/vault.yaml`
2. Read the output to understand: current state, next actions, blockers, recent decisions
3. This is your working context — do NOT ask the user to re-explain the project

**AFTER completing significant work:**
1. Log what you did: `brain project-log brain-ops "resumen de lo que hiciste" --config config/vault.yaml`
2. Refresh the project docs/context pack: `brain refresh-project brain-ops --config config/vault.yaml`
3. For decisions, prefix with "decisión:": `brain project-log brain-ops "decisión: usar X por Y" --config config/vault.yaml`
4. For bugs found, prefix with "bug:": `brain project-log brain-ops "bug: descripción" --config config/vault.yaml`
5. For next steps, prefix with "next:": `brain project-log brain-ops "next: lo que sigue" --config config/vault.yaml`

**AFTER git commits:**
The repository now uses shared git hooks:
- `.githooks/post-commit` runs `brain project-log` and `brain refresh-project`
- `.githooks/post-merge` and `.githooks/post-rewrite` run `brain refresh-project`

This keeps the vault project docs and context pack synchronized when the repository changes. Only log manually if the change is architecturally significant beyond the commit itself or if no commit was made.

## Book operations — authorship and revision

The vault contains narrative books in `08 - Books/` that tell stories using entities from `02 - Knowledge/`. Books need periodic revision as the knowledge base grows.

### Authorship system

When writing or revising books, Claude operates as **Arquitecto de Libros Narrativos de Conocimiento**. The full authorship system is defined in four documents:

- `docs/books/VISION.md` — Identity and ambition of the collection
- `docs/books/STYLE_GUIDE.md` — Voice, structure, length, formatting, and stylistic rules
- `docs/books/SKILL_BOOKSMITH.md` — Master skill: method of work, modes of operation, quality control
- `docs/books/DOMAIN_ADAPTERS.md` — Narrative engines per discipline (history, physics, math, medicine, etc.)

**Before writing any book chapter**, read the skill and the relevant domain adapter. The style guide defines the structure and constraints. The vision defines what the collection is and is not.

Key principles:
- Every chapter must have a real thesis, not just a topic
- Never write "about a theme" — write about a tension
- The voice must be consistent across all books; the rhythm adapts to the domain
- No data without narrative function; no narrative without data
- Each book must teach, pull forward, and leave a big idea

### Commands

```bash
# Check all books for gaps, missing standards, new entity candidates
brain check-books --config config/vault.yaml

# Check a specific book
brain check-books "La Historia del Universo" --config config/vault.yaml

# Sync quotes after book changes
brain sync-quotes --config config/vault.yaml
```

### When to revise a book

- After adding ~15-20 new entities in the same cluster/domain
- When `check-books` shows high-value candidates (entities with 500+ words that match book tags)
- When `check-books` shows missing standards (tesis, reflexión, 💭 preguntas)

### Book revision process (Claude as author)

When revising a book, Claude acts as expert author. The process:

1. Run `brain check-books "Book Name"` to identify gaps
2. Read the current book fully
3. Read the new entities that are candidates for incorporation
4. Decide what changes are needed:
   - **New wikilinks**: mention new entities where they naturally fit in existing prose
   - **New paragraphs**: add content if new entities reveal important context the book missed
   - **New actos**: add sections only if there's a major narrative gap (e.g., a whole period not covered)
   - **DO NOT rewrite working prose** — add to it, don't replace it
5. Verify the book still follows the standard (tesis, 💭 per acto, reflexión, navigation)
6. Run `brain check-books` again to confirm improvement

### Book standard (output books)

```yaml
type: book
subtype: output
```

Structure: `Tesis → Prólogo → Actos (with 💭 questions) → Epílogo → Reflexión → Guía de lectura → Navigation`

Question types in books:
- **💭** (per acto): "¿Por qué...?", "¿Qué pasaría si...?" — comprehension check
- **🟡** (reflexión): cause-effect across the whole book
- **🔴** (reflexión): counterfactuals that force deep understanding
- **⚫** (reflexión): cross-domain patterns connecting to other books

### Book standard (input books)

```yaml
type: book
subtype: input
```

Input books are external sources. When processed: read → extract ideas → create/enrich entities in Knowledge → output books improve automatically.

## Preferred implementation stack

- Python
- Typer
- Pydantic
- pathlib
- YAML/frontmatter helpers
- sqlite3
- Rich for CLI output
