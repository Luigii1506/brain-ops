# Known cleanup debt

Issues discovered during campañas 2.x that are out of their own scope but
need to be tracked so they don't get forgotten. Each entry points at the
campaña / batch that surfaced it and suggests a remediation path.

---

## 1. Kant body wikilink — `[[Ética (Spinoza)|Ética]]`

**Discovered**: Campaña 2.1, Batch F1-consolidation, triple im-01
(`Kant → founded → Ética (Spinoza)`).

**What is wrong**: The note
[`02 - Knowledge/Immanuel Kant.md`](../../../../02%20-%20Knowledge/Immanuel%20Kant.md)
has a body passage that reads:

> Kant fundó la [[Ética (Spinoza)|Ética]] deontológica

The author meant **"ética" as a philosophical discipline**, not Spinoza's
1677 book *Ethica more geometrico demonstrata*. During Campaña 1's
wikify pass, the bare token "ética" in prose was auto-linked, and the
canonicalizer mapped it to the existing entity `Ética (Spinoza)` because
no separate "Ética" (discipline) entity exists. The aliasing via
`|Ética` hides the mismatch visually — the reader sees "Ética" but the
graph points to a book.

Result: `Immanuel Kant.md` contains a body wikilink that claims Kant
founded a book he neither wrote nor had any authorial relationship to.

**Why Campaña 2.1 can't fix it**: 2.1 is frontmatter-only by constraint.
Editing the body to fix the wikilink is a body mutation, which 2.1
explicitly forbids.

**Remediation paths** (pick one in a later campaña):

1. **Narrowest**: edit the single body wikilink in `Immanuel Kant.md`
   to remove the bad link — either `la ética deontológica` (no link)
   or `la [[Ética]] deontológica` if an ethics-discipline entity gets
   created.

2. **Pattern sweep**: audit the vault for `[[Ética (Spinoza)|Ética]]`
   occurrences and fix each. A `brain lint-schemas` rule could flag
   this pattern as suspicious (alias ≠ canonical where the alias is
   a common-noun shorthand).

3. **Create a canonical "Ética" discipline entity**: model ethics as
   a philosophical field (`subtype: discipline`, `domain: filosofia`)
   and re-wikify all bare "ética" mentions to it, keeping
   `Ética (Spinoza)` reserved for references to the book itself. Bigger
   scope, but solves the root cause for other entities in the same
   situation.

**Priority**: medium. The bad wikilink is semantically wrong but does
not corrupt the typed graph — the F1 batch correctly rejected the
derived triple. The main cost is that any future proposer that walks
Kant's body will trip on this same bad wikilink.

**Tracked in**:
- Campaña 2.1 Batch F1-consolidation review
  (`<vault>/.brain-ops/relations-proposals/batch-F1-consolidation/Immanuel Kant.yaml`)
- [CAMPAIGN_2_0_SUMMARY §6.4](CAMPAIGN_2_0_SUMMARY.md) context on the
  same class of issue in the pilot.

---

## 2. Zeus under-typed — pattern extractor insufficient for olympian kinship

**Discovered**: Campaña 2.1, Batch F3-religion (dry-run confirmatorio).

**What is wrong**: The note
[`02 - Knowledge/Zeus.md`](../../../../02%20-%20Knowledge/Zeus.md)
is structurally under-typed for its obvious mythological content.

Current state in SQLite: **1 typed edge** (`located_in → Olimpo`, from
the 2.0 pilot). Nothing else.

What should exist (standard Greek mythology, no interpretation needed):
- `child_of → Cronos`, `child_of → Rea`
- `sibling_of → Poseidón`, `Hades`, `Hera`, `Deméter`, `Hestia`
- `married_to → Hera`
- `parent_of → Atenea`, `Apolo`, `Artemisa`, `Hermes`, `Dioniso`,
  `Heracles`, `Perseo`, and several more

All of those entities exist as canonical notes in the vault. All of
those facts are affirmed by Zeus's own `related:` list. But the body
of the Zeus note writes them in a register the pattern extractor
cannot match. For example:

> *"Zeus es el dios supremo del panteón griego — padre de dioses y hombres"*

The wikilinks `[[Hera]]`, `[[Cronos]]`, `[[Rea]]`, `[[Poseidón]]`,
`[[Hades]]`, etc. all appear in the body (80 total wikilinks), but
none are preceded by a trigger verb within the extractor's 40-60
character window. The note reads as prose essay, not as a structured
genealogy.

Batch F3-religion therefore returned 0 proposals for Zeus
(`skipped: Osiris, Zeus` in the batch stats).

**Why Campaña 2.1 can't fix it**:

1. Body mutation to add `hijo de [[Cronos]]`-style phrasing is out of
   2.1's frontmatter-only constraint.
2. The pattern extractor's `_BODY_TRIGGERS` are conservative by design;
   loosening them for this case would produce many false positives
   elsewhere.
3. 2.1 refuses to type relations not surfaced by the extractor, to
   avoid the "invisible curation" problem where edges appear in SQLite
   without clear YAML provenance.

**Remediation paths** (pick one in a later campaña):

1. **Narrowest — manual typing batch**: produce a hand-curated batch
   `F3.1-zeus-manual` where the olympian kinship edges are written
   directly as proposals (bypassing the pattern extractor) and reviewed
   normally. All facts are mythologically standard — no novel claims.
   Cheapest intervention. Same hash-verify and idempotency guarantees
   as any other batch.

2. **Body enrichment**: rewrite sections of Zeus's body so that the
   kinship predicates are adjacent to their wikilinks (e.g., a
   `## Genealogía` section listing "Hijo de [[Cronos]] y [[Rea]] …").
   Would also benefit the reader. But this is a body mutation and
   should be done with an author-level review, not as 2.x apply.

3. **LLM-assisted semantic extractor (Campaña 2.2 scope)**: an LLM
   reads the prose and proposes the same triples as a human would,
   without requiring syntactic pattern match. Already discussed as
   out-of-scope for 2.1 but a natural 2.2 addition.

**Priority**: medium. Zeus is a central mythological node whose graph
connectivity is currently near-zero. This hurts queries like "who are
the children of Cronos", "who is married to Hera", etc. But it's
isolated — fixing other under-typed deity notes (Hera, Apolo, etc.)
faces the same issue and should be bundled.

**Not specific to Zeus**: the same pattern likely affects other
mythological notes whose bodies are written as essays rather than
structured genealogies. Batch F3-religion confirmed Osiris is well-typed
(identity-first kinship sentences) and Isis moderately so, but any
deity whose body is prose-heavy will be under-typed until option (1)
or (3) runs.

**Tracked in**:
- Campaña 2.1 Batch F3-religion summary:
  `<vault>/.brain-ops/relations-proposals/batch-F3-religion/`
- 2.0 pilot dry-run already flagged Zeus as infra-desarrollada
  with only 1 triple in `Zeus.yaml` Paso 6.

---

## 3. Isaac Newton under-typed — same pattern as Zeus

**Discovered**: Campaña 2.1, Batch F4-science (dry-run confirmatorio).

**What is wrong**: Newton has 71 wikilinks in body (Galileo, Kepler,
Descartes, Relatividad general, Mecánica cuántica, Gravedad, Órbita,
Sistema Solar, Sol, etc.) but the pattern extractor returned 0 new
proposals for him. Current state: **3 typed edges** from the 2.0 pilot
(`influenced_by → Galileo Galilei`, `influenced_by → Johannes Kepler`,
`developed → Física clásica`). Nothing more.

What should exist:
- `author_of → Principia Mathematica` (but Principia isn't a canonical
  entity in the vault — missing)
- `influenced → Albert Einstein` (Einstein's relativity generalized
  Newtonian mechanics; body mentions this)
- `reacted_against → René Descartes` (body mentions the cartesian
  debates)
- `developed → Cálculo diferencial` (as concept, if it existed as
  entity)

The body of Newton is written as an essay, not a structured fact list.
Example:

> *"Su síntesis de la física de [[Galileo Galilei]] y la astronomía de
> [[Johannes Kepler]] bajo un único marco matemático…"*

"Síntesis de" is not a canonical verb trigger; the wikilinks are
grammatical objects detached from predicate-anchoring verbs within the
extractor's window.

**Why Campaña 2.1 can't fix it**: same as Zeus (entry #2) — body
mutation is out of scope, and loosening triggers causes FPs elsewhere.

**Remediation paths**:

1. **Manual typing batch**: write a hand-curated Newton batch with the
   obvious intellectual-history edges. Cheapest.
2. **Create `Principia Mathematica` as a canonical entity** (book,
   1687) and then re-run the proposer — the `author_of` triple would
   then be extractable from passages like "Sus *Principia Mathematica*
   (1687) unificaron…" if a small body tweak adds the wikilink.
3. **LLM-assisted extractor (2.2 scope)**.

**Priority**: baja-media. Newton is a central node in the science
graph, but the science domain is not a primary 2.1 focus. This debt
is best paid off alongside building out Einstein's cluster (entry #4
below).

**Tracked in**: `<vault>/.brain-ops/relations-proposals/batch-F4-science/`

---

## 4. Albert Einstein cluster — 11 missing entities block his graph

**Discovered**: Campaña 2.1, Batch F4-science.

**What is wrong**: Einstein has **2 typed edges** from the pilot
(`developed → Relatividad especial`, `developed → Relatividad general`)
and effectively no other graph connectivity. The F4 batch surfaced 1
additional candidate (`born_in → Ulm`), rejected by priority.

The real problem is that almost every entity Einstein's body links to
does not exist as a canonical vault entity. All of these are
real-world, well-documented, structurally important nodes:

| Missing entity | Relation to Einstein |
|---|---|
| Mileva Marić | primera esposa, colaboradora en sus estudios |
| Elsa Einstein | segunda esposa, compañera en el exilio |
| Marcel Grossmann | colaborador matemático clave en la Relatividad general |
| Max Planck | uno de los primeros defensores dentro del establishment |
| Niels Bohr | interlocutor/rival en los debates fundacionales de QM |
| Arthur Eddington | astrónomo, difusión internacional post-1919 |
| Princeton | sede final (Institute for Advanced Study) |
| Ulm | birthplace (Alemania) |
| ETH Zúrich | formación académica |
| Instituto de Estudios Avanzados | afiliación Princeton 1933-1955 |
| Teoría de la relatividad | concepto general (especial + general) |
| Efecto fotoeléctrico | paper del annus mirabilis 1905, Nobel 1921 |

Creating Ulm alone desbloquearía solo 1 triple. Lo mismo con cualquier
otra entidad individual. El cluster solo desbloquea valor real
**completo**.

**Why Campaña 2.1 can't fix it**: 2.1 scope is priority-limited to
filosofia / historia / religion núcleo (per the plan accepted at the
start of 2.1). Einstein is a ciencia-domain node. Creating 11 entities
for one person is a separate project, not an in-scope 2.1 batch.

**Remediation path** (single recommended):

1. **Campaña 2.x-ciencia — Einstein cluster**: dedicated campaign that
   creates the 11 missing entities en bloque using `brain create-entity`
   or direct-enrich, then runs a `Einstein-cluster-apply` batch that
   types all the newly-resolvable edges in one go. Estimated
   ~20-30 new typed edges across Einstein + each created entity's
   reciprocal relations. Scope probably includes Newton's missing
   entities too (Principia Mathematica) — both under-typed science
   notes are part of the same systemic gap.

No partial remediation makes sense — one-off creations give marginal
return while inflating the creation queue.

**Priority**: baja para 2.1 (outside scope); media-alta como campaña
futura independiente.

**Tracked in**:
- `<vault>/.brain-ops/relations-proposals/batch-F4-science/Albert Einstein.yaml`
- `al-01 Ulm` rejected por prioridad con review_note explícita.

---

## 5. Body ensayístico insuficiente para pattern extractor en filosofía

**Discovered**: Campaña 2.1, Batch Fase1-filosofos-nuevos.

**What is wrong**: Tres notas de filósofos fuera del piloto 2.0 quedaron
skipped (0 proposals) pese a tener body sustancial y contenido
relacional claro:

| Nota | body_chars | unique wikilinks | Formulación típica que no extrae |
|---|---|---|---|
| Averroes | 9,469 | 9 | *"el comentarista más importante de [[Aristóteles]]"* |
| Agustín de Hipona | 15,864 | 22 | *"Nacido en Tagaste"* (Tagaste sin wikilink) |
| Parménides | 13,429 | 18 | *"fundador de la escuela eleática"* (escuela sin wikilink) |

Esto extiende el patrón ya documentado en #2 (Zeus) y #3 (Newton) al
dominio de filosofía. Ninguna de las tres notas es infra-desarrollada
— todas tienen prosa rica. El problema es el **formato de la prosa**:

- "comentarista de X" — no hay predicado canónico exacto; sería
  `influenced_by` con matiz específico, o `interpreted_as` en inverso.
- "fundador de X" — `founded` ES canonical pero el trigger actual del
  extractor es `"fundó"`, no `"fundador de"`. Modificación posible
  del extractor (ver nota más abajo).
- "Nacido en Tagaste" — `born_in` es canonical y el trigger sí dispara,
  pero el target no está wikilinked. Fix upstream: wikilink en body +
  crear entidad Tagaste.

**Why Campaña 2.1 can't fix it en los tres casos**:

- Body mutation para añadir wikilinks fuera de scope.
- Crear entidades masivamente (Tagaste, etc.) fuera de scope de
  Fase 1 actual.
- Extender el catálogo de predicados (ej. `commented_on`) introduciría
  decisiones de taxonomía que no son responsabilidad de 2.1.

**Remediation paths**:

1. **Extractor trigger expansion — `"fundador de"`** (tamaño mini):
   añadir `"fundador de"` como alias de `"fundó"` en `_BODY_TRIGGERS`.
   Desbloquearía al menos Parménides (`founded → Escuela eleática`) y
   probablemente otras figuras que hablan de "fundador" en registro
   biográfico. Propuesta inmediata como mini-subfase después de
   Fase 1 apply, no bloquea el batch actual.
2. **LLM-assisted semantic extractor (Campaña 2.2)**: extrae relaciones
   desde prosa sin depender del patrón exacto.
3. **Body enrichment caso por caso**: wikilinkar "Tagaste", crear
   entidades faltantes, ajustar prosa a formato trigger-friendly. Alto
   costo por nota, mejor resuelto con asistencia LLM.

**Observación general**: esta entrada (+ #2 Zeus + #3 Newton) sugiere
que el pattern extractor actual funciona mejor con notas de "formato
piloto 2.0" (identity-kinship-denso, timeline-estructurado) que con
notas de "formato ensayo histórico-filosófico" (prosa continua con
subordinadas). Escalar 2.1 al resto del vault probablemente requiere
una de las tres remediation paths como paso intermedio.

### Addendum — patrón extendido al dominio historia

Batch `Fase2-romanos-post-augusto` confirmó que el mismo problema
afecta a emperadores romanos en registro narrativo-biográfico:

| Nota | body_chars | Formulación con contenido semántico sin extraer |
|---|---|---|
| Adriano | 6,774 | *"Sucesor de [[Trajano]], abandonó las conquistas en Mesopotamia"* |
| Tiberio | 5,775 | *"Hijastro y sucesor reluctante de [[Augusto]]"* |

Ambos tienen wikilinks **correctamente colocados adyacentes a
sustantivos relacionales** ("Sucesor de", "Hijastro de"), pero estos
sustantivos no son triggers canónicos del extractor actual.

**Candidatos concretos para la siguiente mini-subfase de triggers**:

| Trigger a añadir | Predicado canónico | Desbloquea inmediatamente |
|---|---|---|
| `"sucesor de"`, `"sucesora de"` | `succeeded` | Adriano → Trajano; Tiberio → Augusto |
| `"hijastro de"`, `"hijastra de"` | `adopted_by` (u `child_of` dependiendo de política) | Tiberio → Augusto (hijastro adoptado por Augusto en 4 d.C.) |

Observación especial sobre `"hijastro de"`: mapearlo a `adopted_by`
versus `child_of` es una decisión de política. En el caso romano
"hijastro" en la prosa suele implicar adopción legal posterior. La
mini-subfase debe decidir esto explícitamente antes de añadir el
trigger. Alternativa: emitir como `adopted_by` con `confidence: medium`
para forzar review humano caso por caso.

**Observación adicional** — el predicado `adopted_by` / `adoptive_parent_of`
que introdujimos en Paso 1 no tiene triggers en `_BODY_TRIGGERS`. La prosa
"adoptado por [X]" del body de Nerón (adoptado por Claudio) no disparó
en Fase 2. Añadir `"adoptado por"`, `"adoptada por"`, `"adopted by"`
como triggers de `adopted_by` es otro candidato fuerte para la próxima
mini-subfase.

**Priority**: alta para 2.2 (bloquea el avance real del edge count);
baja para 2.1 actual (no bloquea el cierre).

**Tracked in**:
- `<vault>/.brain-ops/relations-proposals/batch-Fase1-filosofos-nuevos/`
- `Averroes`, `Agustín de Hipona`, `Parménides` aparecen como
  `skipped_empty` en el manifest de la batch.

---

## How to add to this file

When a campaña discovers a cleanup-level issue that is legitimately out
of its scope, append a new section with:

- **Discovered**: which campaña / batch / triple surfaced it
- **What is wrong**: the precise vault state that is broken
- **Why <current campaña> can't fix it**: the scope constraint
- **Remediation paths**: at least two options, narrowest first
- **Priority**: low / medium / high
- **Tracked in**: links to the YAMLs or docs that reference the issue
