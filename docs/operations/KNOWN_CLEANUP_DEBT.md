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

## How to add to this file

When a campaña discovers a cleanup-level issue that is legitimately out
of its scope, append a new section with:

- **Discovered**: which campaña / batch / triple surfaced it
- **What is wrong**: the precise vault state that is broken
- **Why <current campaña> can't fix it**: the scope constraint
- **Remediation paths**: at least two options, narrowest first
- **Priority**: low / medium / high
- **Tracked in**: links to the YAMLs or docs that reference the issue
