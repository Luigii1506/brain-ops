# Campaña 0.5 — Summary

Hardening-only campaign. No vault notes modified. No frontmatter touched.
No entities migrated. The vault and the production DB are byte-identical
before and after Campaña 0.5.

What changed: the system now cannot migrate the production DB as a side
effect of any operation other than the explicit CLI command.

Goal: eliminate the class of bugs exposed during Campaña 0, where running
the full test suite silently applied migration m001 to the real vault DB.

## What Campaña 0.5 delivers

1. **`initialize_entity_tables` no longer migrates.** It only runs the
   current DDL. Pre-existing legacy tables stay as-is until the user runs
   the explicit migration command.
2. **`check_schema_is_current`** — new function that raises
   `SchemaOutOfDateError` with an actionable message when a write path
   hits a legacy DB. Called by `write_extraction_intelligence`.
3. **Two environment variables as guards.**
   - `BRAIN_OPS_NO_MIGRATE=1` → `apply_migrations()` returns `[]` without
     touching the DB.
   - `BRAIN_OPS_BLOCK_REAL_VAULT=1` → `load_validated_vault()` raises
     `RealVaultAccessError` if called on the real vault.
4. **`sys.modules` detection as a second layer.** Even if env vars are
   not set (e.g. unittest discover skipping `__init__.py`), the guards
   inspect `sys.modules` for pytest/unittest markers and activate anyway.
5. **`tests/__init__.py` + `tests/conftest.py`** set the env vars.
6. **`--force-migrate` CLI flag** for the exceptional case where a real
   migration must run under the guards. Still creates a backup.
7. **Two new exception classes:** `SchemaOutOfDateError`,
   `RealVaultAccessError`.
8. **19 new safety tests** asserting the guards are active and
   functional.

## What Campaña 0.5 does NOT do

- Does not modify any vault note.
- Does not migrate any frontmatter.
- Does not change any existing entity.
- Does not touch the production DB schema (already at v1 from Campaña 0).
- Does not introduce any new subtype, predicate, or field.
- Does not execute Campaña 1.

## Files touched

### Modified
- [src/brain_ops/errors.py](../../src/brain_ops/errors.py) — +2 exceptions
- [src/brain_ops/storage/sqlite/entities.py](../../src/brain_ops/storage/sqlite/entities.py) — removed auto-migration; added `check_schema_is_current`
- [src/brain_ops/storage/sqlite/migrations/__init__.py](../../src/brain_ops/storage/sqlite/migrations/__init__.py) — env var + sys.modules guard; `_force` parameter; `force` flag in `migrate_knowledge_db_with_backup`; `blocked` status
- [src/brain_ops/interfaces/cli/runtime.py](../../src/brain_ops/interfaces/cli/runtime.py) — real-vault guard in `load_validated_vault`
- [src/brain_ops/interfaces/cli/knowledge.py](../../src/brain_ops/interfaces/cli/knowledge.py) — presenter reports `blocked` status; accepts `force_migrate`
- [src/brain_ops/interfaces/cli/commands_notes.py](../../src/brain_ops/interfaces/cli/commands_notes.py) — `--force-migrate` flag on CLI
- [tests/test_sqlite_migrations.py](../../tests/test_sqlite_migrations.py) — uses `_force=True` where exercising real migrations

### Created
- [tests/__init__.py](../../tests/__init__.py) — sets guard env vars (primary)
- [tests/conftest.py](../../tests/conftest.py) — sets guard env vars (pytest)
- [tests/test_campaign05_migration_isolation.py](../../tests/test_campaign05_migration_isolation.py) — 12 tests
- [tests/test_campaign05_real_vault_guard.py](../../tests/test_campaign05_real_vault_guard.py) — 7 tests
- [docs/operations/MIGRATIONS.md](MIGRATIONS.md) — migration policy
- [docs/operations/CAMPAIGN_0_5_SUMMARY.md](CAMPAIGN_0_5_SUMMARY.md) — this file

## Safety contract

The contract this campaign establishes and tests enforce:

> **Running the test suite cannot mutate the production DB.**
>
> - `initialize_entity_tables` only runs idempotent DDL — never migrations.
> - `apply_migrations` respects `BRAIN_OPS_NO_MIGRATE=1` and
>   sys.modules-based test runner detection.
> - `load_validated_vault` refuses to open the real vault when the guard
>   is active.
> - Any test that genuinely needs to exercise these paths uses
>   `_force=True` on a temporary DB — never the real one.

The guards are layered so that failure of one does not disable the
contract. In particular, even if `tests/__init__.py` does not run (which
happens under `python -m unittest discover`), the sys.modules detection
still fires.

## How to verify after this campaign

```bash
# 1. Test suite
python -m unittest discover tests
# Expected: 690 tests pass, 11 skipped, 0 failures

# 2. Hash check — DB must be unchanged
sha256sum "/Users/luisencinas/Documents/Obsidian Vault/.brain-ops/knowledge.db" > /tmp/db-pre.sha
python -m unittest discover tests
sha256sum "/Users/luisencinas/Documents/Obsidian Vault/.brain-ops/knowledge.db" > /tmp/db-post.sha
diff /tmp/db-pre.sha /tmp/db-post.sha
# Expected: empty diff

# 3. Explicit migration still works on a real legacy DB
brain migrate-knowledge-db --status --config config/vault.yaml
# Expected: Applied: [1], Pending: (none)
#  (Your DB is already at v1 from Campaña 0.)

# 4. Dry-run purity
brain migrate-knowledge-db --dry-run --config config/vault.yaml
sha256sum "/Users/luisencinas/Documents/Obsidian Vault/.brain-ops/knowledge.db"
# Expected: same hash as before the dry-run
```

## Risks remaining

1. **sys.modules detection is heuristic.** If a non-test program happens to
   have `pytest` or `unittest.loader` imported (e.g. via a plugin), migrations
   will be blocked and the user will see the "blocked" status. Workaround:
   `--force-migrate`. This is the intended trade-off: false positives (block
   when we shouldn't) are safer than false negatives (migrate when we
   shouldn't).

2. **Env var unset in subprocess.** If the test suite spawns subprocesses
   (`subprocess.run(...)`), those subprocesses do NOT inherit the env vars
   unless the test passes `env=os.environ`. If a subprocess then calls the
   migrator on the real DB, it could mutate it. Mitigation: sys.modules
   detection does NOT help here (subprocess has fresh sys.modules). The
   only defense is "tests should not spawn subprocesses that touch the real
   vault". If this becomes a concern, add a third layer: a path allowlist
   check in `apply_migrations` against a tempfile pattern.

3. **`--force-migrate` misuse.** A developer could pass `--force-migrate`
   thinking it's harmless. Mitigation: the help text labels it "exceptional
   use only"; the command output shows the backup path so the user sees
   that something serious happened. Not a perfect mitigation — relying on
   documentation and habit.

4. **Legacy DB user error.** A user with an old DB who doesn't read the
   error message might be confused by `SchemaOutOfDateError`. Mitigation:
   the error text names the exact command to run. The next time they hit
   this, they'll know.

## What's unlocked for Campaña 1

With Campaña 0.5 in place, tests cannot interfere with real-vault data,
and migrations are explicitly gated. Campaña 1 (domain normalization,
historical_event re-subtyping, naming consolidation) can proceed without
worrying about test-suite side effects on the real data.
