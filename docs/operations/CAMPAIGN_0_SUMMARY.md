# Campaña 0 — Summary

Infrastructure-only campaign. No notes in the vault were modified. The vault
is identical before and after Campaña 0. What changed is the system that
reads and writes notes.

See `MASTER_KNOWLEDGE_GRAPH_BLUEPRINT.md` for the full blueprint.

## What Campaña 0 delivers

1. **Taxonomy expanded** — 29 new subtypes covering biology, chemistry, medicine,
   mathematics, language, historical periods / dynasties / processes, and
   esoteric traditions.
2. **Predicate catalog expanded** — ~33 new canonical predicates for intellectual
   reactions, historical transitions, symbolic relations, scientific dependence
   and generic participation.
3. **Naming rules module** — canonical domain slugs (`historia`, `filosofia`,
   `ciencia`, `religion`, `esoterismo`, `machine_learning`) with alias
   detection; capitalization detector for periods / empires; bare-name
   ambiguity detector.
4. **Epistemology layer** — `epistemic_mode` + `certainty_level` vocabulary,
   gating policy for sensitive domains, subtype defaults auto-applied by
   `create-entity`.
5. **Schema validator** — per-subtype required / recommended fields and
   suggested typed relations; violation report.
6. **Schema migrations** — framework + migration m001 that adds `predicate` and
   `confidence` columns to `entity_relations`. Fixes a silent bug where the
   production DB could not store typed predicates.
7. **Two new CLI commands** — `brain lint-schemas` and
   `brain migrate-knowledge-db`.
8. **Extended audit** — `audit-knowledge` now reports `missing_domain`,
   `non_canonical_domain`, `missing_epistemic_mode_gated`,
   `schema_errors_count`, `schema_warnings_count`.

## What Campaña 0 does NOT do

- Does not modify any note in the vault.
- Does not rename entities.
- Does not fill in missing frontmatter.
- Does not type any relation.
- Does not migrate any existing entity.
- Does not block `create-entity` for existing flows (auto-default applies
  where unambiguous; otherwise nothing changes).

Those are Campaña 1 and Campaña 2.

## Files touched

### New files

- `src/brain_ops/domains/knowledge/epistemology.py`
- `src/brain_ops/domains/knowledge/naming_rules.py`
- `src/brain_ops/domains/knowledge/schema_validator.py`
- `src/brain_ops/storage/sqlite/migrations/__init__.py`
- `src/brain_ops/storage/sqlite/migrations/m001_predicate_column.py`
- `docs/operations/NAMING_RULES.md`
- `docs/operations/EPISTEMOLOGY.md`
- `docs/operations/CAMPAIGN_0_SUMMARY.md` (this file)
- `tests/test_epistemology.py`
- `tests/test_naming_rules.py`
- `tests/test_schema_validator.py`
- `tests/test_sqlite_migrations.py`
- `tests/test_campaign0_object_model.py`
- `tests/test_campaign0_create_entity.py`

### Modified files

- `src/brain_ops/domains/knowledge/object_model.py` — new subtypes,
  disambiguation labels, sections, writing guides, predicates, normalizations.
- `src/brain_ops/domains/knowledge/entities.py` — `build_entity_frontmatter`
  now auto-applies epistemic defaults.
- `src/brain_ops/domains/knowledge/knowledge_audit.py` — new coverage
  metrics (domain, epistemic_mode, schema).
- `src/brain_ops/storage/sqlite/entities.py` — `initialize_entity_tables`
  now also runs pending migrations.
- `src/brain_ops/interfaces/cli/knowledge.py` — two new presenters.
- `src/brain_ops/interfaces/cli/commands_notes.py` — two new `@app.command`s.
- `tests/test_cli_command_registration.py` — updated expected commands.

## New commands

### `brain lint-schemas`

Reports schema and naming violations across Knowledge notes. Read-only.

```
brain lint-schemas --config config/vault.yaml
brain lint-schemas --subtype person
brain lint-schemas --domain historia
brain lint-schemas --naming          # include naming-rule violations
brain lint-schemas --strict          # exit code 1 on errors
brain lint-schemas --json            # machine-readable output
```

### `brain migrate-knowledge-db`

Applies pending schema migrations to `knowledge.db`. Always creates a timestamped
backup next to the DB unless `--skip-backup`.

```
brain migrate-knowledge-db --status           # show applied + pending
brain migrate-knowledge-db --dry-run          # list pending without applying
brain migrate-knowledge-db                    # apply pending + backup
brain migrate-knowledge-db --skip-backup      # not recommended
brain migrate-knowledge-db --json             # structured output
```

## How to verify the DB migration safely

The production `knowledge.db` is in `<vault>/.brain-ops/knowledge.db`.
Recommended sequence:

```
# 1. See what would happen (no changes)
brain migrate-knowledge-db --config config/vault.yaml --status
brain migrate-knowledge-db --config config/vault.yaml --dry-run

# 2. Apply (automatic backup)
brain migrate-knowledge-db --config config/vault.yaml

# 3. Verify schema
sqlite3 "<vault>/.brain-ops/knowledge.db" ".schema entity_relations"
# Should show predicate TEXT, confidence TEXT DEFAULT 'medium'

# 4. Verify bookkeeping
sqlite3 "<vault>/.brain-ops/knowledge.db" "SELECT * FROM schema_migrations"
```

The migration is **idempotent**: calling it again is a no-op.

## Baseline lint-schemas report

After `brain migrate-knowledge-db` has run, capture the baseline:

```
brain lint-schemas --config config/vault.yaml --naming --json > /tmp/campaign0-baseline.json
```

This gives the reference point for Campaña 1 (metadata consolidation).

## Risks remaining

- **Substring fallback in `normalize_predicate`** — new predicates with
  common Spanish words (`explica`, `describe`) may substring-match unrelated
  phrases. Regression tests cover the main cases but edge cases may appear
  when ingesting new extractions. Mitigation: tests in
  `test_campaign0_object_model.py`; ad-hoc regressions fixable by reordering.
- **Schema validator runtime on 1047 notes** — scans all `.md` files. For
  the current vault it takes <1s; if the vault grows to 5k+ notes it may
  be worth caching.
- **Backward compatibility of existing entities** — `build_entity_frontmatter`
  now adds `epistemic_mode` automatically for certain subtypes. Existing notes
  are not affected (only newly created ones). No test in the suite breaks on
  this, but it's worth a spot check after migration.
- **SQLite `DROP COLUMN`** — the m001 migration is forward-only. To roll
  back, restore from the automatic backup.

## Next: Campaña 1

Campaña 0 unblocked Campaña 1. With infrastructure in place, Campaña 1 can:

1. Fill `domain` on the 283 notes missing it.
2. Collapse `astronomía` → `ciencia` + `subdomain: astronomia`.
3. Re-subtype the 65 `historical_event` catch-all into
   `historical_period`, `dynasty`, `historical_process`, or puntual event.
4. Resolve bare-name ambiguity (Roma, Tebas, Demóstenes).
5. Normalize capitalization (`Imperio medo` → `Imperio Medo`).
6. Selectively apply `epistemic_mode` where it has highest value first
   (deity, esoteric_tradition, scientific_concept).
