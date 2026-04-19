# Campaña 2.0 — Summary

Infrastructure-only campaign for the typed knowledge graph. Campaña 2.0
delivers the end-to-end plumbing (parser → compile → SQLite → linter → CLI)
and validates it against a 15-note pilot with 71 typed edges. No bulk
migration of `related:` to `relationships:` happens here — that is
Campaña 2.1+.

See [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md) for the format spec and
[`CAMPAIGN_0_SUMMARY.md`](CAMPAIGN_0_SUMMARY.md) /
[`CAMPAIGN_1_OPERATIONS.md`](CAMPAIGN_1_OPERATIONS.md) for the preceding
structural campaigns this builds on.

## Goal

- Make every relation between two entities expressible as a canonical
  typed triple `(source, predicate, object)` with optional `confidence`.
- Persist typed edges in SQLite alongside legacy `related:` fallbacks so
  the graph can be queried by predicate without losing coverage.
- Ship the CLI surface (`query-relations`, `show-entity-relations`)
  needed for humans and agents to interrogate the graph.
- Validate the stack with a real pilot before any bulk migration.

Campaña 2.0 is finished when these five artifacts exist, are tested, and
the pilot compiles cleanly into SQLite — all of which has happened.

## 1. Infrastructure delivered

1. **Typed relation parser**
   [`relations_typed.py`](../../src/brain_ops/domains/knowledge/relations_typed.py).
   `parse_relationships(source, frontmatter) → RelationsParseResult`
   yields a list of `TypedRelation` dataclasses and a list of non-fatal
   errors. Tolerant: malformed entries do not raise, they surface as
   `errors` so the linter can render them.
2. **Compile-time integration**
   [`compile.py`](../../src/brain_ops/domains/knowledge/compile.py).
   `compile_relations_from_frontmatter` reads `relationships:` first,
   falls back to `related:`. Dedup is by target: a target that appears
   typed is not re-emitted as legacy. Multiple typed edges between the
   same source and target are allowed as long as predicates differ
   (dedup key `(source, predicate, object)`).
3. **SQLite persistence of typed fields**
   [`entities.py`](../../src/brain_ops/storage/sqlite/entities.py). The
   INSERT populates `predicate` and `confidence` for typed edges; legacy
   edges from `related:` insert `predicate = NULL`, `confidence = NULL`
   for explicit discriminability.
4. **Linter rules for typed relations**
   [`schema_validator.py`](../../src/brain_ops/domains/knowledge/schema_validator.py).
   Eight checks (see §4) wired into `brain lint-schemas`.
5. **Query layer and CLI**
   [`relations_query.py`](../../src/brain_ops/domains/knowledge/relations_query.py)
   plus the presenters in
   [`knowledge.py`](../../src/brain_ops/interfaces/cli/knowledge.py) and
   the registration in
   [`commands_notes.py`](../../src/brain_ops/interfaces/cli/commands_notes.py).
   Two new commands: `brain query-relations`,
   `brain show-entity-relations`.

### Persistence contract (explicit)

This is what Campaña 2.0 does and does not put into SQLite:

- **SQLite persists today**: `source_entity`, `target_entity`,
  `predicate`, `confidence`, `source_type`.
- **Frontmatter only (not in SQLite)**: `reason`, `date`, `source_id`.
  These are read by the parser, used by the linter, and available to any
  tool that reads the YAML directly. They are not mirrored to
  `entity_relations`.

Promoting `reason` / `date` / `source_id` to columns (or to a sidecar
table) is a 2.x decision and out of scope for 2.0.

## 2. Files created / modified

### Created

- [src/brain_ops/domains/knowledge/relations_typed.py](../../src/brain_ops/domains/knowledge/relations_typed.py) — parser + `TypedRelation` dataclass
- [src/brain_ops/domains/knowledge/relations_query.py](../../src/brain_ops/domains/knowledge/relations_query.py) — `QueriedRelation`, `EntityRelationsSummary`, `query_relations`, `summarize_entity_relations`
- [tests/test_relations_typed_parser.py](../../tests/test_relations_typed_parser.py) — 25 tests
- [tests/test_relations_typed_compile.py](../../tests/test_relations_typed_compile.py) — 23 tests
- [tests/test_relations_typed_linter.py](../../tests/test_relations_typed_linter.py) — 20 tests
- [tests/test_relations_query.py](../../tests/test_relations_query.py) — 16 tests
- [tests/test_show_entity_relations_cli.py](../../tests/test_show_entity_relations_cli.py) — 7 tests
- [docs/operations/CAMPAIGN_2_0_SUMMARY.md](CAMPAIGN_2_0_SUMMARY.md) — this file

### Modified

- [src/brain_ops/domains/knowledge/compile.py](../../src/brain_ops/domains/knowledge/compile.py) — typed-aware compile; dedup by target; `relationships` excluded from metadata
- [src/brain_ops/domains/knowledge/schema_validator.py](../../src/brain_ops/domains/knowledge/schema_validator.py) — `_validate_typed_relations` + `validate_body_relations_divergence`; `validate_vault_notes` builds entity index for cross-note checks
- [src/brain_ops/storage/sqlite/entities.py](../../src/brain_ops/storage/sqlite/entities.py) — INSERT persists `predicate` + `confidence`
- [src/brain_ops/interfaces/cli/knowledge.py](../../src/brain_ops/interfaces/cli/knowledge.py) — `present_query_relations_command`, `present_show_entity_relations_command`
- [src/brain_ops/interfaces/cli/commands_notes.py](../../src/brain_ops/interfaces/cli/commands_notes.py) — `query-relations` and `show-entity-relations` registrations
- [tests/test_cli_command_registration.py](../../tests/test_cli_command_registration.py) — registration assertions for the two new commands
- [docs/operations/RELATIONS_FORMAT.md](RELATIONS_FORMAT.md) — status flipped to *implemented*; persistence contract added; semantic-debt section added; changelog updated
- [CLAUDE.md](../../CLAUDE.md) — new "Typed relations" subsection with persistence contract, query commands, adoption debt marker, and cross-links to this summary

### Vault notes touched by the pilot (15)

`Aristóteles.md`, `Platón.md`, `Sócrates.md`, `Tomás de Aquino.md`,
`Immanuel Kant.md`, `Alejandro Magno.md`, `Augusto.md`, `Julio César.md`,
`Pericles.md`, `Marco Aurelio.md`, `Isis.md`, `Zeus.md`, `Osiris.md`,
`Isaac Newton.md`, `Albert Einstein.md`. Frontmatter-only modification;
body bytes identical to the snapshot
`.brain-ops/backups/02-knowledge-pre-paso6-pilot-20260418-173336/`.

## 3. New CLI commands

### `brain query-relations`

```bash
brain query-relations --from <entity> --config config/vault.yaml
brain query-relations --to <entity> --config config/vault.yaml
brain query-relations --predicate <name> --config config/vault.yaml
brain query-relations --from <entity> --predicate <name> --json
```

At least one of `--from`, `--to`, `--predicate` is required. Default
limit is 1000 rows. Ordered by `(source_entity, predicate IS NULL,
predicate, target_entity)`.

### `brain show-entity-relations`

```bash
brain show-entity-relations "Aristóteles" --config config/vault.yaml
brain show-entity-relations "Aristóteles" --json
brain show-entity-relations "Aristóteles" --only-typed
brain show-entity-relations "Aristóteles" --only-legacy
```

Renders the outgoing and incoming relations of a single entity, grouped
by predicate, with typed and legacy sections. JSON output has
`outgoing.typed_by_predicate`, `outgoing.legacy`, `incoming.*` and
exact counts.

## 4. Active linter rules

Wired into `schema_validator._validate_typed_relations` and surfaced via
`brain lint-schemas`:

| Rule                                 | Severity | Check                                                                 |
|--------------------------------------|----------|-----------------------------------------------------------------------|
| `relation_unknown_predicate`         | error    | Predicate not in `CANONICAL_PREDICATES`                               |
| `relation_missing_field`             | warning  | Entry is missing `predicate` or `object`                              |
| `relation_invalid_shape`             | warning  | Entry is not a YAML mapping                                           |
| `relation_invalid_confidence`        | info     | `confidence` not in `{high, medium, low}`                             |
| `relation_self`                      | warning  | Subject references itself                                             |
| `relation_duplicate`                 | info     | Same `(source, predicate, object)` appears twice in one note          |
| `relation_object_missing`            | warning  | Object is not an existing entity (needs entity_index)                 |
| `relation_object_is_disambig_page`   | warning  | Object points to a disambiguation_page (needs entity_index)           |
| `relation_body_divergent` (separate) | info     | Body `## Relationships` references entities diverging from frontmatter. Checked by `validate_body_relations_divergence`, not emitted by the standard loop. |

None blocks compilation.

## 5. Pilot result

- **Notes modified**: 15 / 15 (all targeted)
- **Files modified outside pilot**: 0
- **Body byte-drift across pilot**: 0
- **Frontmatter drift outside the new `relationships:` block**: 0
- **Typed rows in `entity_relations` (`predicate IS NOT NULL`)**: **71**
- **Confidence distribution**: 68 `high`, 3 `medium`
- **Predicates used**: 22 distinct canonical predicates
- **Tests**: 861 pass, 12 skipped (migration guards)
- **Snapshot**: `.brain-ops/backups/02-knowledge-pre-paso6-pilot-20260418-173336/`

Distribution by source entity:

```
Aristóteles:3  Platón:4  Sócrates:4  Tomás:4  Kant:4
Alejandro:7  Augusto:6  JulioCésar:7  Pericles:4  MarcoAurelio:5
Isis:8  Zeus:1  Osiris:9  Newton:3  Einstein:2   Total: 71
```

Spot-check (`brain show-entity-relations Aristóteles --json`):

```
out.typed=3  in.typed=4  out.legacy=1198
out:  studied_under→Platón  reacted_against→Platón  mentor_of→Alejandro Magno
in:   Platón→mentor_of,  Alejandro→studied_under,
      Tomás→influenced_by,  Kant→influenced_by
```

Both triples to `Platón` (`studied_under` + `reacted_against`) survive
because the dedup key is `(source, predicate, object)`, not
`(source, object)`.

## 6. Known limitations

### 6.1 Adoption is semantic debt, not resolved in 2.0

The pilot ships three adoptive edges using biological predicates:

- `Augusto       → child_of  → Julio César`
- `Julio César   → parent_of → Augusto`
- `Marco Aurelio → child_of  → Antonino Pío`

Each carries the annotation `reason: adoptive — refinar con predicado
específico de adopción si se introduce` in frontmatter. The annotation
**lives in YAML only** — SQLite stores `predicate = child_of` /
`parent_of` with no distinction between biological and adoptive. A
future campaña introducing a dedicated predicate (e.g. `adopted_by` /
`adopted_child_of`) can migrate these edges deterministically by
matching the `reason` marker in frontmatter. Campaña 2.0 does not
resolve this; it only documents it. See
[`RELATIONS_FORMAT.md` §12.1](RELATIONS_FORMAT.md).

### 6.2 Annotation fields not queryable from SQLite

`reason`, `date`, `source_id` are defined, parsed, and preserved in
frontmatter, but are not mirrored to `entity_relations`. Queries on
these fields must go through the YAML, not the relational store.

### 6.3 Body `## Relationships` drift is informational only

The linter emits `relation_body_divergent` as `info`, not a blocker.
The pilot is frontmatter-only (no body `## Relationships` section), so
this gap is not exercised.

### 6.4 Canonical entity gaps are common

The pilot dry-run identified 18 objects referenced by prose but missing
as canonical entities (e.g. `Liceo`, `Teofrasto`, `Mileva Marić`,
`Max Planck`, `Batalla de Alesia`). Triples to missing objects were
omitted from the pilot. This is a queue for `create-entity` or
renaming — not a Campaña 2.0 bug.

### 6.5 Graph inference / transitive closure is not done

Stored facts only. No "all mentees of A transitively" — that is an
explicit downstream query, not a materialised relation. See
[`RELATIONS_FORMAT.md` §11](RELATIONS_FORMAT.md).

## 7. Proposal for Campaña 2.1 — guided migration

Goal: take the ~16,700 `related:` entries in the vault and migrate the
**typeable fraction** (estimated 30-50%) to `relationships:`, leaving
the rest as `related:` fallback.

### 7.1 Scope

Subtypes with the clearest typing patterns go first:

1. **`person`** in `domain ∈ {historia, filosofia, ciencia}`
   — rich biographical/intellectual predicates (`child_of`,
   `studied_under`, `mentor_of`, `author_of`, `influenced_by`,
   `allied_with`, `opposed`, `fought_in`).
2. **`deity`** in `domain = religion`
   — kinship-heavy graph (`child_of`, `sibling_of`, `married_to`,
   `parent_of`, `opposed`, `appears_in`).
3. **`book`** and **`scientific_concept`**
   — mostly `author_of` / `developed` with `part_of_system`,
   `depends_on`.

Low priority for 2.1: abstract concepts (`Libertad`, `Justicia`,
`Ética`) and disambiguation pages — their relational semantics are
looser and not clearly typeable.

### 7.2 Proposed deliverables

1. **`brain propose-relations <entity>`** — a read-only command that,
   for a target entity, generates a dry-run proposal of triples by
   mining the body prose, the `related:` list, and cross-references
   in other notes. Outputs the same shape as the Paso 6 dry-run:
   `subject, predicate, object, confidence, evidence source`. No file
   modification.
2. **`brain apply-relations <entity> [--dry-run]`** — applies an
   approved proposal (or the most recent dry-run) frontmatter-only,
   idempotent, body-safe.
3. **Batch runner**: `brain migrate-relations --subtype person
   --domain filosofia --batch-size 20` — iterates through candidate
   notes, generates proposals, requests approval per batch, applies,
   and runs `compile-knowledge` at the end of each batch.
4. **Safety**: every batch takes a pre-snapshot under
   `.brain-ops/backups/` and verifies body byte-identity after apply.
   Post-step is `brain compile-knowledge` (frontmatter-only operation,
   same as Paso 6 — no `brain reconcile`).
5. **Dedicated adoption predicate** (optional, decided before 2.1
   starts): introduce `adopted_by` / `adopted_child_of` in
   `CANONICAL_PREDICATES`. If accepted, migrate the three pilot
   adoptive edges by `reason` marker as the first 2.1 subtask.

### 7.3 Success criteria for 2.1

- ≥ 500 new typed edges with ≥ 90% `confidence: high`
- Zero body drift in any migrated note
- Zero drift outside the target subtype per batch
- Full test suite passes after each batch
- `brain show-entity-relations` returns richer, meaningful views for
  any person/deity/book note in the migrated set

### 7.4 Explicitly out of scope for 2.1

- Mirroring `reason` / `date` / `source_id` to SQLite — defer to 2.2
- Transitive queries / graph inference
- Auto-typing via LLM without human approval per batch
- Touching the `related:` field itself on legacy entries — coexistence
  remains the rule

## 8. Tests delivered

Campaña 2.0 adds **91 new tests** across five files, all passing as
part of the 861-test suite:

| File                                    | Tests |
|-----------------------------------------|-------|
| `tests/test_relations_typed_parser.py`  | 25    |
| `tests/test_relations_typed_compile.py` | 23    |
| `tests/test_relations_typed_linter.py`  | 20    |
| `tests/test_relations_query.py`         | 16    |
| `tests/test_show_entity_relations_cli.py` | 7   |

Plus registration assertions in `tests/test_cli_command_registration.py`.

## 9. Safety contract

- No body bytes changed in any pilot note.
- No frontmatter field changed outside the newly inserted
  `relationships:` block in any pilot note.
- No file outside the 15 pilot notes changed.
- Migration of `knowledge.db` still requires explicit
  `brain migrate-knowledge-db` — Campaña 2.0 only calls
  `compile-knowledge`, which rebuilds the tables without running
  migrations (see [`MIGRATIONS.md`](MIGRATIONS.md)).
- Snapshot + hash-diff protocol used for the pilot and to be reused
  verbatim in every 2.1 batch.
