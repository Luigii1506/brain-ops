# Campaña 1 — Operational policy

Operational rules for bulk consolidation operations on the vault.

## The problem this document solves

Before Campaña 1 started, running `brain reconcile` after any bulk edit
produced two kinds of body changes:

1. **Wikify** — converted plain-text mentions into `[[wikilinks]]`.
2. **Cross-enrich** — added missing entities to "Related notes" sections.

Both are useful in steady state, but during bulk consolidation they cause
two problems:

- **Wikify + ambiguous bare names = semantic corruption.** Before the bare
  name `Ética` was disambiguated, wikify linked every mention of "la Ética
  kantiana" / "la Ética utilitarista" to `[[Ética (Spinoza)|Ética]]` — the
  book by Spinoza, which has nothing to do with Kant or utilitarianism.
- **Opaque scope.** A subfase that claims to be "frontmatter-only" has its
  post-step silently editing bodies. The contract is broken.

## Post-step rule — one table, one decision

| Subfase type                                                              | Post-step                                                |
|--------------------------------------------------------------------------|----------------------------------------------------------|
| Frontmatter-only (domain aliases, fill-domain, epistemic_mode, subtype)  | `brain compile-knowledge`                                |
| Rename / disambiguation (capitalization fixes, bare-name disambig)       | `brain reconcile --skip-wikify --skip-cross-enrich`      |
| Post-Campaña-1, optional re-linking                                       | `brain reconcile` (default — wikify + cross-enrich on)   |

### Why this split

- `brain compile-knowledge` is **body-safe by definition**. It only reads
  frontmatter and writes SQLite. Never mutates any `.md`. Does NOT sync
  the registry (not needed when the frontmatter didn't add/remove entities).
- `brain reconcile --skip-wikify --skip-cross-enrich` is **body-safe by
  contract** (see test `tests/test_campaign1_reconcile_skip_flags.py`).
  It syncs the registry and compiles SQLite — needed when entity names
  change (rename, disambiguation) but we still don't want body edits.
- Default `brain reconcile` is fine once the vault's bare names are all
  disambiguated. Only resume using it AFTER Subfase 1.5 completes.

## What the skip flags guarantee

The test `ReconcileSkipFlagsTestCase.test_both_skip_flags_leave_bodies_byte_exact`
captures bytes of every `.md` in a realistic fixture vault before and after
running `reconcile --skip-wikify --skip-cross-enrich`. It asserts
byte-identical snapshots. If that test ever fails, the contract is broken.

The complementary test `ReconcileDefaultBehaviorRegressionTestCase`
protects the default behavior from regressing — without the flags,
wikify still runs.

## When default reconcile is safe to run again

After Subfase 1.5 (bare-name disambiguation) is complete and the vault has
no remaining `bare_name_ambiguity` violations per `brain lint-schemas --naming`.

Until then, never run `brain reconcile` without both skip flags during
campaign work. If you run it by accident, restore from the snapshot taken
immediately before the operation, re-run `compile-knowledge` to resync
SQLite, and continue.

## Snapshot policy (vault without git)

The user's vault is not under git. Before every `--apply` during Campaña 1:

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
SNAPSHOT="/Users/.../Obsidian Vault/.brain-ops/backups/02-knowledge-pre-<subfase>-${STAMP}"
cp -rp "/Users/.../Obsidian Vault/02 - Knowledge" "$SNAPSHOT"
```

Restore is simple: `cp -rp "$SNAPSHOT"/* ".../02 - Knowledge/"` (or use a
Python diff-aware restore to preserve partial progress, as happened in the
Lote 1 incident).

## Body-change audit procedure

After every `--apply` + post-step, verify no unintended body changes by
hashing the entire `02 - Knowledge` tree before and after:

```bash
python3 -c "
from pathlib import Path; import hashlib
h = hashlib.sha256()
for md in sorted(Path('<vault>/02 - Knowledge').rglob('*.md')):
    h.update(md.read_bytes())
print(h.hexdigest())
"
```

For a frontmatter-only subfase, the hash after `compile-knowledge` must
match the hash right after the frontmatter edit (before compile). If they
differ, compile wrote something — investigate before continuing.

## Revised Campaña 1 order (after Lote 1 incident)

The incident on 2026-04-17 reordered the campaign. The new order is:

1. **1.1** — domain aliases (philosophy/history/science → canonical)
2. **1.2** — astronomía → ciencia (done alongside 1.1)
3. **1.5** — bare-name disambiguation (MOVED UP; eliminates the semantic
   hazards that made `reconcile` unsafe)
4. **1.3** — capitalization fixes (requires renames)
5. **1.4a** — fill-domain auto (~200 notes)
6. **1.4b** — fill-domain manual review (~91 notes)
7. **1.6** — re-subtype `historical_event` (65 notes)
8. **1.7** — `epistemic_mode` backfill (~310 notes)

Rationale for the reorder: Subfase 1.5 removes the bare-name ambiguity
that makes `reconcile --with-wikify` semantically unsafe. Once 1.5 is
done, it *would* be safe to resume default reconcile usage — but we
still don't, because the remaining subfases are also frontmatter-only.
