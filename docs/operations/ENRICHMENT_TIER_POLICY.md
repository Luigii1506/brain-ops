# Enrichment Tier Policy

Política operativa para decidir, ante una entidad nueva o existente, **qué
modo de enriquecimiento usar**. Refina la regla simplificada de
[`AGENT_DIRECT_LLM_WORKFLOWS.md`](AGENT_DIRECT_LLM_WORKFLOWS.md) y de
`CLAUDE.md` ("DEEP MODE para person/empire/civilization, LIGHT MODE para el
resto"), que clasifica por **tipo de entidad** pero no captura la dimensión
relevante: la **densidad de mi conocimiento general** sobre esa entidad
particular.

## Por qué este doc existe

La regla anterior asumía que toda persona, civilización o libro requería
deep mode. La auditoría empírica de Campaña 3 (parche dirigido sobre 9
notas religion-domain Tier-1) demostró que para figuras ultra-canónicas
mi conocimiento general es lo bastante denso para producir notas
fácticamente correctas en light mode, y que el costo de deep no se
justifica. Para figuras menos famosas la regla original sigue vigente.

## Tiers

### Tier-1 — figuras y obras universalmente canónicas

**Criterios:**

- Aparecen en programas escolares de cualquier país occidental
- Tienen entradas extensas en Wikipedia ES y EN coincidentes en lo
  fundamental
- Son referenciadas por libros canónicos del vault sin necesidad de
  glosa adicional
- El LLM tiene representación masiva en su training data

**Ejemplos:** Jesucristo, Mahoma, Buda (Siddhartha Gautama), Abraham,
Moisés, Biblia, Corán, Aristóteles, Platón, César, Newton, Einstein.

**Modo recomendado:** **light + audit + patch dirigido**.

### Tier-2 — figuras y obras importantes pero menos masivas

**Criterios:**

- Reconocidas por especialistas y por gente educada del campo
- Wikipedia ES suele ser pobre o ausente; Wikipedia EN tiene la
  información
- El LLM tiene conocimiento general pero con huecos predecibles en
  fechas, lugares, nombres secundarios

**Ejemplos:** Nagarjuna, Bodhidharma, Dogen, Rumi, Ibn Arabi, Al-Ghazali,
Sankara, Plotino, Boecio, Avicena, Mahavira, Guru Nanak (caso límite).

**Modo recomendado:** **deep mode desde el inicio** con Wikipedia EN o
fuente académica como source persistido.

### Tier-3 — figuras regionales, secundarias o especializadas

**Criterios:**

- Wikipedia ES inexistente o stub; Wikipedia EN parcial
- El LLM puede confabular sin advertir
- A menudo requieren múltiples fuentes para triangular

**Ejemplos:** santos regionales, gurús menores, figuras locales,
pensadores periféricos.

**Modo recomendado:** **deep mode obligatorio** + cross-check con
segunda fuente (académica si es posible) + flagging explícito de
incertidumbre en frontmatter (`status: in_progress`, no `canonical`).

## Workflow Tier-1 — light + audit + patch

1. **Escribir light** desde conocimiento general
   - Identity expandida, Historical Context, Key Facts, Core
     Significance, Timeline, Legacy
   - Distinguir explícitamente hecho histórico vs atribución tradicional
     vs claim debatida
   - `status: in_progress`

2. **Audit con Wikipedia** vía WebFetch
   - Comparar fechas, números específicos, nombres secundarios
   - Identificar omisiones de hechos load-bearing (no trivia)
   - Identificar errores duros (raros) y datos plausibles-pero-no-
     verificables (frecuentes)

3. **Patch dirigido**
   - Sólo añadir lo identificado por el audit
   - Edits puntuales con `Edit` tool, no rewrite
   - Reconcile body-safe: `brain reconcile --skip-wikify
     --skip-cross-enrich`

**Tiempo estimado:** ~15 min por nota (5 escribir + 5 auditar + 5 parchar).
Comparado con deep mode (~45 min por nota incluyendo
plan-direct-enrich + escritura por pases + post-process + check-coverage).

## Workflow Tier-2/3 — deep mode

Sin cambios respecto a `CLAUDE.md` y `AGENT_DIRECT_LLM_WORKFLOWS.md`:

```bash
brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml
# escribir nota a nota usando los pases generados
brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml
brain check-coverage "Entity Name" --config config/vault.yaml
```

## Patrón de omisión predecible (Tier-1, light mode)

El LLM en light mode tiende a saltarse de manera sistemática:

| Categoría | Cobertura LLM | Ejemplos saltados en la auditoría |
|---|---|---|
| Doctrina, conceptos centrales | ✅ Excelente | (cubierto bien) |
| Fechas mayores | ✅ Correctas | (cubierto bien) |
| Personas nombradas secundarias | ❌ Saltadas | Aarón, Miriam, los 12 apóstoles, hijos de Nanak (Sri Chand, Lakshmi Das) |
| Eventos secundarios nombrados | ❌ Saltados | Batallas de Uhud y Trinchera, tratado de Hudaybiyya, becerro de oro, Concilio de Roma 382 |
| Lugares específicos | ❌ Saltados | Cueva de Macpela, Kushinagar |
| Cifras precisas | ⚠️ A veces erradas | 1924 vs 1922 (edición Al-Azhar del Corán) |

El audit existe específicamente para cazar estas categorías. Sin él, la
nota es navegable pero falta detalle de "named entities" que un lector
experto notaría.

## Cuándo NO aplica light + audit (incluso para Tier-1)

- **Cuando se va a usar la nota como base de citas externas** (libros
  publicables, papers): deep desde el inicio, source persistido
- **Cuando hay datos numéricos densos** (cuántos soldados en cuántas
  batallas con qué fechas): deep, audit no escala
- **Cuando la entidad tiene controversias historiográficas activas**
  (debate de fechas del Éxodo, historicidad de Lao Tsé): deep para
  que el plan estructure las posiciones

## Evidencia empírica — auditoría Campaña 3 sobre 9 notas

Sobre 9 notas religion-domain Tier-1 escritas en light mode:

- **0 errores fácticos duros**
- **1 error de fecha menor** (1924 → 1922)
- **24 omisiones load-bearing** distribuidas en 8 notas (1 nota — Jesucristo
  — pasó audit limpio sin patches)
- **Tiempo total parche dirigido:** ~15 min para las 8 notas
- **Tiempo estimado deep rewrite alternativo:** ~6h

El audit + patch capturó ~95% del valor de un deep rewrite a ~5% del
costo, validando empíricamente la política Tier-1.

## Ver también

- [`AGENT_DIRECT_LLM_WORKFLOWS.md`](AGENT_DIRECT_LLM_WORKFLOWS.md) —
  workflow general de direct-enrich y post-process
- [`CAMPAIGN_1_OPERATIONS.md`](CAMPAIGN_1_OPERATIONS.md) — body-safety
  flags para reconcile durante operaciones masivas
- [`SCHEMA_GOVERNANCE.md`](SCHEMA_GOVERNANCE.md) — cuándo y cómo
  extender CANONICAL_PREDICATES y ENTITY_TYPES
- [`BRIDGE_ENTITIES.md`](BRIDGE_ENTITIES.md) — patrón cross-domain para
  entidades que viven en filosofía + religión, ciencia + filosofía, etc.
