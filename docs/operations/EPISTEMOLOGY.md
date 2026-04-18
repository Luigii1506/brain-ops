# Epistemic layer

Every knowledge note can declare what kind of truth claim it represents.
This exists because the vault covers domains with very different warrant
structures — verified science, documented history, religious tradition,
symbolic esoterism, open speculation — and mixing them unmarked erodes
the meaning of every assertion.

Implementation: `src/brain_ops/domains/knowledge/epistemology.py`.

## Fields

### `epistemic_mode` (enum)

| Value            | When to use                                                     |
|------------------|-----------------------------------------------------------------|
| `historical`     | Documented historical facts, persons, events                    |
| `scientific`     | Empirically supported scientific knowledge                       |
| `religious`      | Religious doctrine, sacred texts, official teachings            |
| `mythological`   | Myths, deities, stories within a mythological tradition          |
| `esoteric`       | Esoteric traditions, occult, symbolic systems                    |
| `philosophical`  | Philosophical arguments, concepts, schools                       |
| `speculative`    | Open hypotheses, uncertain attributions                          |

### `certainty_level` (enum, optional)

Orthogonal to `epistemic_mode`. Answers: how solid is this claim within
its own frame?

| Value               | Meaning                                                      |
|---------------------|--------------------------------------------------------------|
| `well_supported`    | Robust consensus or strong evidence within the frame         |
| `tradition_based`   | Grounded in a tradition (religious, scholarly, esoteric)     |
| `symbolic`          | Claim operates at a symbolic rather than factual level       |
| `contested`         | Real dispute between serious positions                       |
| `speculative`       | Informed guesswork, minority view, reconstruction            |

### `tradition` (string, recommended for religious / esoteric / mythological)

The specific tradition the note belongs to. Examples:
- Religion: `cristianismo`, `islam`, `budismo theravada`
- Mythology: `mitología griega`, `mitología egipcia`
- Esoteric: `hermetismo`, `cábala`, `alquimia medieval`

## Gating policy

For NEW notes created via `create-entity` in these domains, `epistemic_mode`
is required (`error` severity when `--strict` is set):

- `religion`
- `esoterismo`
- `filosofia`
- `ciencia`

`create-entity` auto-applies the subtype default when possible (see
`DEFAULT_EPISTEMIC_BY_SUBTYPE` in `epistemology.py`). If the subtype has no
default, the writer sets it explicitly.

For EXISTING notes, missing `epistemic_mode` is always a **warning**, never
an error — migration is gradual.

## Default by subtype

| Subtype                                                       | Default          |
|--------------------------------------------------------------|------------------|
| `deity`, `myth`, `mythological_place`                        | `mythological`   |
| `esoteric_tradition`, `ritual`, `symbolic_system`,           |                  |
| `divination_system`, `mystical_concept`, `esoteric_text`,    | `esoteric`       |
| `occult_movement`                                            |                  |
| `philosophical_concept`, `school_of_thought`                 | `philosophical`  |
| `scientific_concept`, `theorem`, `mathematical_object`,      |                  |
| `mathematical_function`, `constant`, `mathematical_field`,   |                  |
| `proof_method`, `chemical_element`, `compound`, `molecule`,  | `scientific`     |
| `biological_process`, `gene`, `disease`, `medical_theory`,   |                  |
| `cell`, `cell_type`, `organism`, `species`,                  |                  |
| `anatomical_structure`                                       |                  |
| `historical_event`, `historical_period`,                     |                  |
| `historical_process`, `dynasty`                              | `historical`     |
| `sacred_text`                                                 | `religious`      |

Subtypes **without** a default (must choose explicitly):
`person`, `war`, `battle`, `city`, `country`, `book`, `paper`, `civilization`,
`polity`, `empire`, all disambiguation pages.

## Usage in queries

Once `epistemic_mode` is populated, queries can filter by kind of truth:

```
brain lint-schemas --domain ciencia --json | jq '.schema.per_subtype'
```

Or in natural ask-driven searches, restrict to `epistemic_mode=historical`
when asking "what happened in 323 a.C.?" versus `epistemic_mode=mythological`
when asking "how did Zeus kill the Titans?".
