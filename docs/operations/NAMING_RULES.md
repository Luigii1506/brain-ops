# Naming rules — Knowledge entities

Canonical conventions for naming entities, domains, and disambiguated notes.
Detectors live in `src/brain_ops/domains/knowledge/naming_rules.py`. Violations
are **reported by `brain lint-schemas --naming`**, never auto-fixed.

## 1. Domain slugs

All `domain:` frontmatter values MUST be one of the canonical slugs:

| Canonical slug     | Meaning                             |
|--------------------|-------------------------------------|
| `historia`         | Historia (todas las épocas)         |
| `filosofia`        | Filosofía                           |
| `ciencia`          | Ciencia natural y formal            |
| `religion`         | Religión, mitología, cultos         |
| `esoterismo`       | Esoterismo, tradiciones simbólicas  |
| `machine_learning` | Machine learning / IA aplicada      |

Slugs are **español sin acentos** except `machine_learning` which is
convention of the field.

### Aliases (detected, collapsed on migration)

| Observed value     | Canonical collapse       | Suggested subdomain |
|--------------------|--------------------------|---------------------|
| `history`          | `historia`               | —                   |
| `philosophy`       | `filosofia`              | —                   |
| `science`          | `ciencia`                | —                   |
| `religión`         | `religion`               | —                   |
| `filosofía`        | `filosofia`              | —                   |
| `astronomía`       | `ciencia`                | `astronomia`        |
| `astronomia`       | `ciencia`                | `astronomia`        |
| `esoteric`         | `esoterismo`             | —                   |

Migration is **Campaña 1**, not Campaña 0. The linter currently reports
aliased domains as warnings, nothing more.

## 2. Capitalization of period / empire / dynasty names

Pattern: `<head noun> <adjective>` where the adjective MUST start capitalized.

Head nouns tracked:
`Imperio`, `Período`, `Periodo`, `República`, `Reino`, `Dinastía`, `Edad`,
`Era`, `Siglo`.

| Bad                      | Good                     |
|--------------------------|--------------------------|
| `Imperio romano`         | `Imperio Romano`         |
| `Imperio medo`           | `Imperio Medo`           |
| `Período arcaico griego` | `Período Arcaico griego` |

Fixes are **manual** (Campaña 1).

## 3. Bare-name disambiguation

A bare name (no suffix) that coexists with disambiguated variants
`Nombre (etiqueta)` MUST be a `disambiguation_page`.

Examples of bare names that should become disambiguation pages:
- `Tebas` → coexists with `Tebas (Egipto)`
- `Demóstenes` → coexists with `Demóstenes (orador)`, `Demóstenes (general)`

Bare-name ambiguity is detected vault-wide:

```
brain lint-schemas --naming
```

Report includes `bare_name_ambiguity` violations with all variants listed.

### When the bare name is correct

- No ambiguity exists → bare is fine.
- There is one **dominant, stable** meaning and the ambiguity is marginal.
- The bare is already a `disambiguation_page` — no violation.

## 4. Person names (Spanish canonical form)

- Use the Spanish form when it exists: `Platón`, `Aristóteles`, `Julio César`,
  `Cicerón`, `Homero`.
- For names with no Spanish translation, keep the original: `Martin Heidegger`,
  `Simone de Beauvoir`.
- Disambiguation suffix in Spanish: `(persona)`, `(dios)`, `(planeta)`.

## 5. Subdomain naming

Free-form but recommended: español sin acentos, snake_case or space-separated,
e.g. `ancient greece`, `mitologia griega`, `information_retrieval`. Keep one
convention per domain.
