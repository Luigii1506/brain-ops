# Database migrations — operational policy

Policy and mechanics for migrating the production `knowledge.db` schema.

Implementation: `src/brain_ops/storage/sqlite/migrations/`.
Safety tests: `tests/test_campaign05_migration_isolation.py`,
`tests/test_campaign05_real_vault_guard.py`.

## The golden rule

**Migrations on the real DB only happen when you explicitly run
`brain migrate-knowledge-db`.** Nothing else — no import, no test, no
workflow side effect — can apply a migration to the production DB.

## When migrations run

| Context                              | Does it migrate? |
|--------------------------------------|------------------|
| User runs `brain migrate-knowledge-db` | ✅ Yes          |
| User runs `brain migrate-knowledge-db --dry-run` | ❌ No |
| User runs `brain migrate-knowledge-db --status`  | ❌ No |
| `brain compile-knowledge`, `brain reconcile`, ...| ❌ No |
| `write_compiled_entities(db_path, ...)` is called | ❌ No |
| `write_extraction_intelligence(db_path, ...)` is called | ❌ No, but raises `SchemaOutOfDateError` on legacy schemas |
| `initialize_entity_tables(db_path)` is called    | ❌ No, only DDL idempotent |
| `apply_migrations(db_path)` is called            | ❌ No (guarded) |
| `apply_migrations(db_path, _force=True)`         | ✅ Yes (internal only) |
| Test suite runs (pytest or unittest)              | ❌ No (guarded) |

## Guards (two layers, belt-and-suspenders)

### Layer 1 — Environment variables

| Variable                       | Effect when `=1`                        |
|--------------------------------|------------------------------------------|
| `BRAIN_OPS_NO_MIGRATE`         | `apply_migrations()` returns `[]` immediately |
| `BRAIN_OPS_BLOCK_REAL_VAULT`   | `load_validated_vault()` raises `RealVaultAccessError` if called with the default `config/vault.yaml` |

These are set automatically in `tests/__init__.py` and `tests/conftest.py`.

### Layer 2 — `sys.modules` detection

Even if the env vars are not set (e.g. `python -m unittest discover` skips
`__init__.py` of the tests package), the guards detect test runners by
inspecting `sys.modules` for these markers:

- `pytest`, `_pytest` — pytest is active
- `unittest.loader`, `unittest.runner` — unittest is actively discovering/running

These modules are only present during test execution, not when an app uses
`from unittest import TestCase` for type purposes only.

## Normal user flow

```
# 1. Check state
brain migrate-knowledge-db --status --config config/vault.yaml

# 2. Preview pending migrations
brain migrate-knowledge-db --dry-run --config config/vault.yaml

# 3. Apply — automatic backup before ALTER TABLE
brain migrate-knowledge-db --config config/vault.yaml

# Output includes:
#   Backup: .../knowledge-backup-<timestamp>-pre-migration.db
#   Status: migrated
#   Applied migrations:
#     1  Add predicate and confidence columns to entity_relations @ 2026-...
```

The backup is a bit-identical copy. To roll back: restore it over the
live DB.

## Exceptional: `--force-migrate`

```
brain migrate-knowledge-db --force-migrate --config config/vault.yaml
```

Bypasses both the env var guard and the `sys.modules` detection. This
is intended for cases like:

- Debugging the migration system itself
- CI pipelines that legitimately need to migrate a test DB
- Scripts that need to migrate a fresh vault programmatically

Invariants that `--force-migrate` preserves:

- Automatic backup still runs (unless `--skip-backup` is also passed).
- Migration still runs inside a transaction; failure → rollback.
- `schema_migrations` bookkeeping is still updated.

**Never use `--force-migrate` without `--dry-run` first**, unless you
know exactly what you're doing.

## Legacy DB behavior

If the production DB is on a pre-Campaña-0 schema (missing `predicate`/
`confidence`), any write path that depends on those columns fails fast:

```
brain reconcile --config config/vault.yaml
# Error: SchemaOutOfDateError: Knowledge DB at <path> is missing columns
# ['confidence', 'predicate'] in entity_relations. Run
# `brain migrate-knowledge-db --config <path>` to upgrade the schema.
```

This is intentional: silent schema divergence would be worse than a clear error.

## Verifying the DB was not touched

Paranoid verification after running the test suite:

```bash
sha256sum "<vault>/.brain-ops/knowledge.db" > /tmp/db-pre.sha
python -m unittest discover tests
sha256sum "<vault>/.brain-ops/knowledge.db" > /tmp/db-post.sha
diff /tmp/db-pre.sha /tmp/db-post.sha  # must be empty
```

If the diff is non-empty, a test touched the real DB. Report it as a
safety regression.

## Writing a new migration

1. Add a new file `src/brain_ops/storage/sqlite/migrations/mNNN_description.py`
   with `VERSION`, `DESCRIPTION`, `up(conn)`, and optional `down(conn)`.
2. Append it to the `MIGRATIONS` tuple in `migrations/__init__.py`.
3. Add a test in `tests/test_sqlite_migrations.py` that exercises `up()`
   on a temp DB with `apply_migrations(db, _force=True)`.
4. Run `python -m unittest discover tests` — all should pass.
5. Document the migration in this file under "Migration history".
6. User validates on their own DB via:
   `brain migrate-knowledge-db --dry-run --config config/vault.yaml`

## Migration history

| Version | Description                                                    |
|---------|----------------------------------------------------------------|
| 1       | Add `predicate` and `confidence` columns to `entity_relations` |
