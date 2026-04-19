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

## How to add to this file

When a campaña discovers a cleanup-level issue that is legitimately out
of its scope, append a new section with:

- **Discovered**: which campaña / batch / triple surfaced it
- **What is wrong**: the precise vault state that is broken
- **Why <current campaña> can't fix it**: the scope constraint
- **Remediation paths**: at least two options, narrowest first
- **Priority**: low / medium / high
- **Tracked in**: links to the YAMLs or docs that reference the issue
