# Relations format — Canonical specification

Spec for how typed relationships between entities are represented in the vault,
queried from SQLite, and migrated from the legacy untyped `related:` field.

**Status**: Campaña 2.0 implemented (parser, compile, linter, CLI, pilot).
**Last updated**: 2026-04-18 (post-pilot).

---

## 1. Goal

Every relation between two entities in the knowledge graph should be:

- **Typed** with a canonical predicate from the 75+ vocabulary defined in
  [`object_model.py`](../../src/brain_ops/domains/knowledge/object_model.py)
  (`CANONICAL_PREDICATES`).
- **Queryable** from SQLite with exact predicate match.
- **Narratable** in a way that a human reading the note understands not just
  THAT two entities are related but WHY and with what role.
- **Gradually migratable**: legacy `related:` stays as fallback; typing is
  incremental, not a big-bang rewrite.

---

## 2. The hybrid format (Option C)

A relationship has two representations that must stay in sync:

### 2.1 Frontmatter — structural source of truth

```yaml
---
name: Aristóteles
subtype: person
domain: filosofia
epistemic_mode: philosophical
relationships:
  - {predicate: studied_under, object: Platón}
  - {predicate: mentor_of, object: Alejandro Magno}
  - {predicate: author_of, object: Ética a Nicómaco}
  - {predicate: reacted_against, object: Platón}
  - {predicate: founded, object: Liceo}
  - {predicate: influenced, object: Tomás de Aquino}
related:
  - Eudoxo de Cnido
  - Teofrasto
---
```

Each entry is a YAML dict with two required keys (`predicate`, `object`).
Optional keys can be added per entry as needed:

| Key         | Required | Type   | Persisted in SQLite | Purpose                                          |
|-------------|----------|--------|---------------------|--------------------------------------------------|
| `predicate` | yes      | string | **yes** (`predicate` column)          | One of `CANONICAL_PREDICATES`                    |
| `object`    | yes      | string | **yes** (`target_entity` column)      | Canonical entity name (must exist or be mention) |
| `confidence`| no       | string | **yes** (`confidence` column)         | `high` / `medium` (default) / `low`              |
| `reason`    | no       | string | no — frontmatter only                 | One-line justification                           |
| `date`      | no       | string | no — frontmatter only                 | When the relation holds                          |
| `source_id` | no       | string | no — frontmatter only                 | Pointer to ingested source                       |

> **Persistence note (2.0)**: SQLite today stores `predicate` and `confidence`
> alongside `source_entity` / `target_entity`. The annotation fields (`reason`,
> `date`, `source_id`) live in the frontmatter and are not mirrored to SQLite.
> They are available to any tool that reads the YAML directly. Promoting any
> of them to SQLite columns is a 2.x decision, not in scope for 2.0.

The short inline-dict form `- {predicate: X, object: Y}` is preferred for
compactness; expand to multi-line when extra keys are added:

```yaml
relationships:
  - predicate: reacted_against
    object: Platón
    reason: Crítica a la teoría de las Formas
    confidence: high
  - predicate: influenced
    object: Tomás de Aquino
    reason: Vía la recepción árabe (Averroes)
```

### 2.2 Body section — narrative layer (optional)

A markdown section `## Relationships` renders the frontmatter content in
human-readable prose. Same relations, richer context:

```markdown
## Relationships

- `studied_under` **[[Platón]]** — Alumno 367-347 a.C. en la Academia.
- `reacted_against` **[[Platón]]** — Crítica central a la teoría de las Formas:
  "*amigo de Platón, pero más amigo de la verdad*".
- `mentor_of` **[[Alejandro Magno]]** — Tutor real 343-336 a.C. en Pella.
- `founded` **[[Liceo]]** — Escuela en Atenas, 335 a.C.
- `influenced` **[[Tomás de Aquino]]** — Vía la mediación árabe ([[Averroes]]);
  base del aristotelismo escolástico.
```

**Convention**: each bullet starts with the predicate in backticks, then the
entity wikilink, then an em-dash, then the narrative justification.

### 2.3 Legacy `related:` field — fallback

```yaml
related:
  - Eudoxo de Cnido
  - Teofrasto
```

`related:` remains valid and keeps working. Entries there are treated as
**untyped** relations — compiled to SQLite with `predicate = NULL` (equivalent
to `related_to`). Campaña 2 migrates what's typeable; the rest can stay as
`related:` forever.

---

## 3. Rule of authority

When frontmatter `relationships:` and body `## Relationships` disagree, the
**frontmatter wins** for tooling. The body is for humans.

The linter may flag divergence (extra wikilinks in body that aren't in
frontmatter, or vice versa) but **does not block** compilation. In practice,
the flow is:

1. Writer edits frontmatter `relationships:` — this is the grafo.
2. Writer keeps body `## Relationships` in sync as narrative companion.
3. `compile-knowledge` reads ONLY frontmatter.
4. Linter warns on divergence. Writer decides if they want to fix.

If you only maintain one of them, **always maintain the frontmatter**. The
body is optional polish.

---

## 4. Directionality

Relations are written **from the subject's perspective**. The subject is
always the note owner. The object is always the other entity.

Example from `Aristóteles.md`:
```yaml
relationships:
  - {predicate: studied_under, object: Platón}   # Aristóteles studied under Platón
```

Example from `Platón.md`:
```yaml
relationships:
  - {predicate: mentor_of, object: Aristóteles}   # Platón was mentor of Aristóteles
```

Both notes describe the SAME real-world relation, each from its own angle.
The graph stores them as two separate typed edges (which is correct — each is
a legitimate, directional assertion from its source).

**Do not duplicate bidirectionally within one note.** Do not write
`influenced` AND `influenced_by` pointing to the same entity inside
`Aristóteles.md` — pick the one that matches the subject's perspective.

### When an explicit inverse predicate exists, use it

The catalog has paired inverses for common biographical/intellectual roles:

| Forward        | Inverse          |
|----------------|------------------|
| `mentor_of`    | `studied_under`  |
| `parent_of`    | `child_of`       |
| `influenced`   | `influenced_by`  |
| `preceded_by`  | `preceded`       |
| `caused`       | `caused_by`      |

### When no inverse exists, use the natural direction

The catalog intentionally does NOT have inverses for every predicate (e.g.
`developed`, `conquered`, `founded` have no `developed_by`, `conquered_by`,
`founded_by`). Write from whichever side is natural for the note.

From `Relatividad general.md`:
```yaml
relationships:
  - {predicate: developed, object: Albert Einstein}
```
Read as: *Relatividad general was developed by Einstein.* The `developed`
predicate is bidirectional-capable through SQL queries; no need for
`developed_by`.

---

## 5. What counts as a valid object

Three cases, all accepted:

1. **Existing canonical entity**: `object: Platón` (the exact `name` of
   another note). Most common case.
2. **Disambiguated form**: `object: Tebas (Grecia)` (canonical disambiguated
   name, since `Tebas` is a disambiguation_page).
3. **Mention**: a name for an entity that doesn't have its own note yet.
   This is fine — the compile step registers it as a `mention` in the
   registry. When someone later creates that note, the edge becomes active.

### Never reference via the disambiguation page

❌ `object: Tebas` — refers to the disambiguation_page, which is a navigation
   aid, not an entity.
✅ `object: Tebas (Grecia)` or `object: Tebas (Egipto)` — the specific variant.

The linter flags disambiguation_page references as warnings.

---

## 6. Examples by domain

### 6.1 Philosophy

```yaml
---
name: Aristóteles
subtype: person
domain: filosofia
relationships:
  - {predicate: studied_under, object: Platón}
  - {predicate: mentor_of, object: Alejandro Magno}
  - {predicate: reacted_against, object: Platón}
  - {predicate: author_of, object: Ética a Nicómaco}
  - {predicate: author_of, object: Metafísica (Aristóteles)}
  - {predicate: founded, object: Liceo}
  - {predicate: influenced, object: Tomás de Aquino}
related:
  - Eudoxo de Cnido
---
```

### 6.2 History

```yaml
---
name: Augusto
subtype: person
domain: historia
relationships:
  - {predicate: succeeded, object: Julio César}
  - {predicate: allied_with, object: Marco Antonio}
  - {predicate: opposed, object: Marco Antonio}
  - {predicate: founded, object: Alto Imperio romano}
  - {predicate: conquered, object: Egipto}
  - {predicate: preceded, object: Tiberio}
related:
  - Cleopatra VII
  - Lépido
---
```

The `allied_with → opposed` pair with the same object captures a real
historical arc: first alliance (Second Triumvirate, 43 a.C.), later enemy
(post-Accio, 31 a.C.). The body `## Relationships` section is the right place
to narrate this.

### 6.3 Religion / mythology

```yaml
---
name: Isis
subtype: deity
domain: religion
epistemic_mode: mythological
tradition: mitología egipcia
relationships:
  - {predicate: married_to, object: Osiris}
  - {predicate: parent_of, object: Horus}
  - {predicate: sibling_of, object: Seth}
  - {predicate: sibling_of, object: Neftis}
  - {predicate: worshipped_by, object: Antiguo Egipto}
  - {predicate: appears_in, object: Mito de Osiris}
related:
  - Hathor
  - Ra
---
```

### 6.4 Science

```yaml
---
name: Relatividad general
subtype: scientific_concept
domain: ciencia
epistemic_mode: scientific
relationships:
  - {predicate: developed, object: Albert Einstein}
  - {predicate: reacted_against, object: Gravedad newtoniana}
  - {predicate: part_of_system, object: Física moderna}
  - {predicate: explains, object: Agujero negro}
  - {predicate: explains, object: Expansión del universo}
  - {predicate: depends_on, object: Espacio-tiempo}
---
```

---

## 7. Predicates — canonical vocabulary

The full vocabulary is in
[`object_model.py`](../../src/brain_ops/domains/knowledge/object_model.py)
under `CANONICAL_PREDICATES`. High-level groups:

| Group                          | Count | Examples                                         |
|--------------------------------|-------|--------------------------------------------------|
| Biographical                   | 7     | `born_in`, `parent_of`, `married_to`             |
| Intellectual                   | 14    | `studied_under`, `influenced`, `reacted_against` |
| Political / Military           | 9     | `ruled`, `conquered`, `fought_in`, `allied_with` |
| Historical transitions         | 7     | `belongs_to_period`, `emerged_from`              |
| Organizational / Spatial       | 8     | `part_of`, `located_in`, `capital_of`            |
| Temporal / Causal              | 5     | `caused`, `preceded`, `occurred_in`              |
| Religious / mythological       | 8     | `worshipped_by`, `symbolizes`, `appears_in`      |
| Work                           | 6     | `author_of`, `depicts`, `argues_for`             |
| Scientific                     | 6     | `explains`, `depends_on`, `part_of_system`       |
| Generic participation          | 1     | `participated_in`                                 |
| Classification / fallback      | 5     | `instance_of`, `related_to`                      |

If a predicate you need is missing, raise it as a candidate. Do not invent
ad-hoc predicates — the fallback is `related_to` (untyped) until the catalog
gains the new predicate formally.

---

## 8. Migration from `related:`

Current state: the vault has ~16,700 entries in `related:` across all notes.
Campaña 2 will migrate a fraction (estimated 30-50%) to typed
`relationships:`. The rest stays in `related:`.

Workflow per note:

1. Read the note's body and current `related:` list.
2. For each entry in `related:`, determine if it maps to a clear predicate
   based on context (subtype of both ends, body text, known patterns).
3. Move typeable entries to `relationships:` with the right predicate.
4. Leave uncertain entries in `related:` (fallback remains valid).
5. Optionally write or expand the `## Relationships` body section.

Tooling for this is the scope of **Campaña 2.0** (infrastructure —
delivered) and **Campaña 2.1+** (guided migration — see
[`CAMPAIGN_2_0_SUMMARY.md`](CAMPAIGN_2_0_SUMMARY.md) §7).

### Coexistence rule

Frontmatter may have both `relationships:` and `related:` simultaneously. An
entity object can even appear in both (e.g., same note has
`{predicate: influenced, object: X}` AND `X` in `related:`). This is
ambiguous but not wrong — the compile step deduplicates: typed relations
take precedence, untyped `related:` entries whose object already appears in
`relationships:` are skipped.

**Rule**: once typed, remove from `related:`. But this is a cleanup nicety,
not a correctness requirement.

---

## 9. SQLite mapping

`entity_relations` table already has the columns needed (migration m001,
Campaña 0):

```sql
CREATE TABLE entity_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    predicate     TEXT,          -- canonical predicate or NULL for legacy
    confidence    TEXT DEFAULT 'medium',
    source_type   TEXT
)
```

`compile-knowledge` behavior (implemented in Campaña 2.0):

- For each entry in frontmatter `relationships:`, write a row with
  `predicate` populated and `confidence` copied from the frontmatter (default
  `medium` if absent).
- For each entry in `related:` whose target does NOT already appear as a
  typed target in `relationships:`, write a row with `predicate = NULL` and
  `confidence = NULL` (legacy). Deduplication is by **target**: if the same
  target appears both typed and legacy, only the typed row is written.
- Multiple typed edges between the same source and target are allowed as
  long as the predicates differ. Dedup key is `(source, predicate, object)`.
- `reason` / `date` / `source_id` are read by the parser for linting purposes
  but **not written** to `entity_relations`. They stay in the YAML.

Query example (populated):
```sql
-- Who did Aristóteles teach?
SELECT target_entity FROM entity_relations
WHERE source_entity = 'Aristóteles' AND predicate = 'mentor_of';

-- All intellectual influences on Tomás de Aquino
SELECT source_entity FROM entity_relations
WHERE target_entity = 'Tomás de Aquino' AND predicate = 'influenced';
```

---

## 10. Linter rules for typed relations (implemented — Campaña 2.0)

Active in `schema_validator._validate_typed_relations` and surfaced via
`brain lint-schemas`:

| Rule                                 | Severity | Check                                                                   |
|--------------------------------------|----------|-------------------------------------------------------------------------|
| `relation_unknown_predicate`         | error    | Predicate not in `CANONICAL_PREDICATES`                                 |
| `relation_missing_field`             | warning  | Entry is missing `predicate` or `object`                                |
| `relation_invalid_shape`             | warning  | Entry is not a mapping                                                  |
| `relation_invalid_confidence`        | info     | `confidence` value not in `{high, medium, low}`                         |
| `relation_self`                      | warning  | Subject references itself                                               |
| `relation_duplicate`                 | info     | Same `(source, predicate, object)` triple appears twice in one note     |
| `relation_object_missing`            | warning  | Object is not an existing entity nor a known mention (needs entity_index) |
| `relation_object_is_disambig_page`   | warning  | Object points to a disambiguation_page (needs entity_index)             |
| `relation_body_divergent` (separate) | info     | Body `## Relationships` section references an entity not in frontmatter (or vice versa). Checked by `validate_body_relations_divergence` — not emitted by the standard validator loop. |

None of these block compilation. Entity-resolution checks
(`relation_object_missing`, `relation_object_is_disambig_page`) require
`validate_vault_notes` to build the entity index in the first pass.

---

## 11. What this format does NOT do (on purpose)

- **No graph inference**. If Aristóteles `studied_under` Platón, the system
  does not auto-generate `mentor_of` in Platón's note. Both sides must be
  written by the author (or tooling) explicitly.
- **No transitive closure**. If A `mentor_of` B and B `mentor_of` C,
  querying "all mentees of A" does not return C. That is an explicit
  downstream query, not a stored fact.
- **No temporal reasoning**. `date:` is a string annotation, not a validated
  temporal field.
- **No versioning of relations**. A relation either exists or doesn't. No
  "was-true-until-X" semantics. If a relation changes (Augusto allied, later
  opposed Marco Antonio), write two separate relations; the narrative in
  body explains the arc.

---

## 12. Known semantic debt (2.0)

Campaña 2.0 ships a usable typed-graph infrastructure, but leaves the
following refinements **unresolved**. They are intentionally deferred and
tracked here so future campañas pick them up from the same source of truth.

### 12.1 Adoption — resolved in Campaña 2.1 Paso 1 *(historical)*

Originalmente, el piloto 2.0 envió tres edges adoptivos con
predicados biológicos (`child_of` / `parent_of`) anotados con
`reason: adoptive …`. Campaña 2.1 Paso 1 introdujo los predicados
canónicos dedicados `adopted_by` y `adoptive_parent_of`, y migró los
tres edges byte-level:

- `Augusto       → adopted_by         → Julio César`   *(was child_of)*
- `Julio César   → adoptive_parent_of → Augusto`       *(was parent_of)*
- `Marco Aurelio → adopted_by         → Antonino Pío`  *(was child_of)*

Los triples quedan persistidos en SQLite con los predicados
adoptivos canónicos; el marcador `reason: adoptive` se eliminó como
parte de la migración. Ver
[`CAMPAIGN_2_1_SUMMARY.md`](CAMPAIGN_2_1_SUMMARY.md) §1 para el
detalle de la migración.

La sección se conserva como referencia histórica — explica por qué
los predicados adoptivos existen en `CANONICAL_PREDICATES`.

### 12.2 Annotation fields are not queryable from SQLite

`reason`, `date`, `source_id` are defined in the format but do not reach the
relational store. Any query that needs "all edges where `reason` mentions X"
must go through the YAML, not `entity_relations`. Promoting these to columns
(or to a sidecar `entity_relation_annotations` table) is a 2.x decision.

### 12.3 Body-frontmatter divergence is not enforced

The linter has the check (`relation_body_divergent` / 
`validate_body_relations_divergence`) but it's informational only. A note
can have a typed frontmatter and a legacy body `## Relationships` that
diverges, and compilation proceeds. The pilot of 15 notes is
frontmatter-only (no body `## Relationships` section in Campaña 2.0), so
this gap is not exercised yet.

---

## 13. Changelog

- **2026-04-19 (Campaña 2.1 closure)** — Operational validation phase
  closed with +17 typed edges (88 total), 6 batches + 2 mini-subfases
  de triggers, 59 new tests, 6 structured debts identified and
  documented. Extractor gained nominal-form triggers for `founded`,
  `succeeded`, `adopted_by`. Adoption debt from §12.1 resolved at the
  predicate level with new canonical predicates `adopted_by` /
  `adoptive_parent_of`. See
  [`CAMPAIGN_2_1_SUMMARY.md`](CAMPAIGN_2_1_SUMMARY.md) for full closure
  narrative, bottleneck analysis, and 2.2 proposal.
- **2026-04-18 (post-pilot)** — Campaña 2.0 infrastructure shipped: parser
  (`relations_typed.py`), compile/SQLite persistence of `predicate` +
  `confidence`, schema linter rules, `brain query-relations`,
  `brain show-entity-relations`. Pilot applied to 15 notes (71 typed
  edges). Adoption flagged as semantic debt (§12.1).
- **2026-04-18** — initial spec approved.
