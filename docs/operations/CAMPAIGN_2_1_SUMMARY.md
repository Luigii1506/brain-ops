# Campaña 2.1 — Summary

**Operational validation phase.** 2.1 exercised the 2.0 typed-relations
infrastructure on real vault content, across 6 domain batches and 2
incremental extractor improvements. The phase delivered exactly what
it was designed to verify — end-to-end process correctness, zero body
drift, disciplined review loop — and, in the process, discovered that
the real bottleneck for expanding the typed graph is neither
infrastructure nor review capacity, but three structural properties
of the vault content itself.

Campaña 2.1 ends not because it hit its original 400-edge target
(it didn't, and the reasons are now well-documented), but because
that target was a proxy for the wrong question. The right question
turned out to be: *where does the pattern extractor stop working, and
why?* — and 2.1 answered it with evidence.

See [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md) for the underlying
format spec and [`CAMPAIGN_2_0_SUMMARY.md`](CAMPAIGN_2_0_SUMMARY.md)
for the infrastructure campaign this builds on. Accumulated cleanup
debt is tracked separately in
[`KNOWN_CLEANUP_DEBT.md`](KNOWN_CLEANUP_DEBT.md).

---

## 1. What 2.1 delivered

### Infrastructure (Pasos 1–4)

| Paso | Module | Delivered |
|---|---|---|
| 1 | `object_model.py` | `adopted_by` + `adoptive_parent_of` canonical predicates; 3 pilot adoptive edges migrated byte-level |
| 2 | `relations_proposer.py` | Read-only pattern-based proposer with 17 canonical-predicate triggers, hedging-aware confidence, cross-ref evidence via SQLite, object-status resolution |
| 3 | `relations_applier.py` | Frontmatter-only apply with per-entity atomic + per-batch sequential model, SHA-verified pre/post body and non-block frontmatter |
| 3.1 | same | Guided manual rollback on abort (applied / aborted / not_processed lists + copy-pasteable restore commands) |
| 4 | `relations_batch.py` | Batch-propose-relations with manifest, per-entity YAMLs, `missing_entities.md`, `summary.md` |

Incidental fix in Paso 1: `.brain-ops` added to the `_ALWAYS_EXCLUDED`
set in `list_vault_markdown_notes`. Previously backup snapshots were
being scanned as live entities, inflating compile counts by roughly
16×.

### Batches applied

| Batch | Subtype/Domain | Notes touched | Edges written | Reject rate |
|---|---|---|---|---|
| F1-consolidation | person/filosofia (pilot) | 3 / 5 | 4 | 59% |
| F2-history | person/historia (pilot) | 3 / 5 | 7 | 68% |
| F3-religion | deity/religion (pilot) | 0 / 3 | **0** (no-op) | 100% |
| F4-science | person/ciencia (pilot) | 0 / 2 | **0** (no-op) | n/a |
| Fase1-filosofos-nuevos | person/filosofia (non-pilot) | 2 / 5 | 2 | 33% |
| Fase2-romanos-post-augusto | person/historia (non-pilot) | 2 / 5 | 3 | 20% |
| Mini-subfase #2 re-apply | historia (re-run with new triggers) | 1 / 5 | 1 | 33% |

### Mini-subfases de triggers

| Mini-subfase | Triggers añadidos | Predicado | Edges desbloqueados |
|---|---|---|---|
| #1 | `"fundador de"`, `"fundadora de"`, `"founder of"` | `founded` | 0 directos (`fundador de` disparó 1 FP atrapado en review) |
| #2 | `"sucesor de"`, `"sucesora de"`, `"adoptado por"`, `"adoptada por"` | `succeeded`, `adopted_by` | 1 (Adriano → Trajano) |

### Tests

Tests nuevos de 2.1 sobre la base 2.0:

| Archivo | Tests (total) | Origen 2.1 |
|---|---:|---|
| `test_relations_proposer.py` | 23 | Paso 2 (16) + mini #1 (3) + mini #2 (4) |
| `test_relations_applier.py` | 22 | Paso 3 (19) + Paso 3.1 rollback (3) |
| `test_relations_batch.py` | 11 | Paso 4 (11) |
| `test_relations_typed_linter.py` | +3 | Paso 1 adoptive predicates |

Total añadidos en 2.1: **59 tests nuevos**. Suite final:
**920 passed, 12 skipped** (0 failures, 0 errors en toda la campaña).

## 2. Métricas finales

### Typed edges

| Hito | Edges |
|---|---|
| Pre-2.1 (post-pilot 2.0) | 71 |
| Post-adoptive migration (Paso 1) | 71 (migración de predicado) |
| Post-F1-consolidation | 75 |
| Post-F2-history | 82 |
| Post-F3/F4 (no-op) | 82 |
| Post-Fase1-filosofos-nuevos | 84 |
| Post-Fase2-romanos-post-augusto | 87 |
| Post-mini-subfase #2 re-apply | **88** |

**Net: +17 typed edges. 100% high confidence.**

### Safety invariants (cumplidos sin excepción)

- Body byte drift incidents: **0** en las 7 ejecuciones de apply
- Drift outside batch manifest: **0** archivos no-manifest modificados
- Tests rompiendo tras apply: **0**
- Regresiones de triples del piloto 2.0: **0**

### Entidades con typed edges nuevas fuera del piloto

5 entidades "desbloqueadas" — estrenaron sus primeros typed edges en 2.1:

- Alberto Magno (Fase 1)
- Pitágoras (Fase 1)
- Claudio (Fase 2)
- Trajano (Fase 2)
- Adriano (mini-subfase #2)

### Creation queue

9 entidades priorizadas en
`<vault>/.brain-ops/relations-proposals/creation-queue.md`:

| Priority | Entities |
|---|---|
| Alta (5) | Estagira, Liceo, Alcmeónidas, Jantipo, Pela |
| Media (3) | Calcis, Pericles el Joven, Agripina la Menor |
| Baja (1) | Bucéfala |

Crearlas todas desbloquearía 8 triples adicionales ya aprobados y
bloqueados por `MISSING_ENTITY`.

### Deudas documentadas

6 entradas estructuradas en
[`KNOWN_CLEANUP_DEBT.md`](KNOWN_CLEANUP_DEBT.md):

1. Kant body wikilink mal canonicalizado
2. Zeus under-typed — pattern extractor insuficiente
3. Newton under-typed — same patrón que Zeus
4. Einstein missing cluster (11 entidades)
5. Body ensayístico en filosofía (Averroes, Agustín, Parménides) + addendum historia (Adriano, Tiberio)
6. Matcher de string exacto — adverbios intercalados rompen match (Tiberio)

## 3. Lo que funcionó bien

### Arquitectura de revisión humano-primero

Reject rates entre 20% y 68% según dominio demostraron que **el review
humano no es opcional, es el único que puede filtrar FPs de pattern
extraction**. La arquitectura que lo permite — propose → YAML
editable por humano → apply con filtros duros — resultó robusta. El
operador (yo actuando como reviewer) puede leer, aprobar/rechazar, y
cambiar targets canónicos sin romper la auditabilidad.

### Idempotencia y rollback

Cada batch se aplicó al menos una vez; varios re-regeneraron YAMLs y
re-aplicaron con cero side-effects fuera del manifest. La política
"already-typed filter + body byte-hash" hizo la idempotencia
trivialmente observable.

### Guided manual rollback (Paso 3.1)

El protocolo operativo decidido en Paso 3 ("no auto-rollback, sí
reporte guiado") no se ejercitó en producción — ningún batch abortó
— pero los 3 tests dedicados verifican que el reporte de abort entrega
exactamente lo que un humano necesitaría para decidir el restore
(applied / aborted / not_processed + comandos copy-pasteables con
shlex-quoted paths).

### Creation queue con prioridades explícitas

Poner prioridades alta/media/baja y documentar qué triples desbloquea
cada entidad convierte la cola en un plan de trabajo, no un backlog
indefinido. 8 entradas de cola con desbloqueo cuantificado (5 edges
alta, +2 media, +1 baja) se sienten gestionables.

### Operational unit: mini-subfase

Acuñar "mini-subfase" como commit autónomo entre batches — una
mejora de 15-50 LoC + tests + regen de un batch específico — resultó
una buena unidad de trabajo. Las 2 mini-subfases ejecutadas (#1
founded nominal, #2 succession + adoption) cada una confirmó o
rechazó una hipótesis concreta en un solo ciclo.

### Dedup multi-predicado `(source, predicate, object)`

La decisión de diseño de 2.0 (que un par `(source, object)` pueda
tener varios predicados) fue validada en producción con el par
`Augusto allied_with + opposed Marco Antonio` de F2. Captura el arco
histórico real. Sin esa decisión, el batch habría forzado elegir uno
de los dos predicados.

## 4. Lo que no escaló como se esperaba

### El objetivo de 400 edges asumía un vault más homogéneo

El objetivo se formuló al inicio de 2.1 como "mínimo 400 edges
nuevos en toda la campaña". Asumía implícitamente que los batches
posteriores a la consolidación del piloto rendirían a razón de
~10-15 edges nuevos cada uno, aplicando la misma curación que el
piloto (71 edges en 15 notas).

La realidad que los 6 batches no-piloto expusieron:

- **Pattern extractor tiene ratio de recall muy dependiente del
  formato del body**. Notas de "formato piloto 2.0" (identity denso +
  timeline estructurado) rinden 5-10 edges. Notas de "formato ensayo
  histórico-filosófico" (prosa continua con subordinadas) rinden 0-2
  edges.
- **Aproximadamente 60% de las notas fuera del piloto** tienen el
  segundo formato. No es bug de las notas — es estilo narrativo
  legítimo. Pero el extractor no lo cubre sin modificaciones.
- **Muchas relaciones obvias están bloqueadas por MISSING_ENTITY,
  no por falta de detection**. Einstein es el caso paradigmático: 11
  entidades faltantes que bloquearían alrededor de 20 triples si
  existieran. Crearlas una a una tiene coste marginal bajo; en
  cluster, coste alto.

El objetivo numérico no se alcanzó (88 vs. 471+). Pero la razón por
la que no se alcanzó **no es una falla del proceso de 2.1** — es un
descubrimiento del proceso. Sin ejecutar batches en 6 dominios
distintos con review humano riguroso, no sabríamos dónde está el
piso real del rendimiento.

### Triggers nominales tienen ROI menor al esperado en aislamiento

Las dos mini-subfases añadieron 7 triggers nuevos. Efecto directo: 1
edge desbloqueado (Adriano → Trajano). Efecto indirecto: 1 FP
introducido (Claudio → Guardia Pretoriana), atrapado en review.

ROI de triggers individuales es bajo porque **la mayoría de las
notas que fallan en pattern extraction fallan por múltiples razones**
(essay format + wikilink ausente + adverbio intercalado) que se
componen. Resolver una sola causa raramente desbloquea la nota
completa.

Caso concreto Tiberio: "Hijastro y sucesor reluctante de [[Augusto]]"
— falla por 2 razones separadas. Triggers de Paso 2 pueden cubrir
`hijastro de` y `sucesor reluctante de`, pero el segundo requiere
**matcher regex**, no solo un trigger más.

### La idempotencia del batch regen no preserva review history

Cuando se regenera un batch con `--overwrite` tras mejoras del
extractor, los `review_note: rejected` de la curación previa se
pierden. FPs ya conocidos reaparecen y deben re-revisarse. En 2.1
pasó con `Claudio cl-01 → Guardia Pretoriana` (rechazado 2 veces).
No es grave (el review es barato), pero es un impuesto no previsto.

Una mejora para 2.2: `--preserve-reviews` flag que mantiene status
+ review_note de regens previos matching por `(id, predicate, object)`.

## 5. Deudas acumuladas (dónde buscar más detalle)

Cada deuda en `KNOWN_CLEANUP_DEBT.md` trae:
- Qué está mal (con ubicación exacta en el vault)
- Por qué 2.1 no podía arreglarlo (política o scope)
- 2-4 remediation paths (narrowest first)
- Priority (baja/media/alta)

Las 6 entradas están estructuradas para que 2.2 pueda elegir un
subconjunto como scope-de-campaña sin re-descubrir el contexto.

## 6. Por qué 2.2 cambia de estrategia

2.1 operó bajo la hipótesis: *"infraestructura + pattern extraction +
review humano disciplinado serán suficientes para escalar el typed
graph"*.

Las 6 deudas documentadas convergen a una hipótesis revisada:
*"pattern extraction es suficiente para notas de formato canónico,
pero ~60% del vault no tiene ese formato"*. Los tres mecanismos
estructurales que bloquean el avance son:

1. **Matcher rígido del extractor** (deuda #6)
   Afecta transversalmente a todos los triggers nominales.
   Desbloquearlo con regex-tolerance **multiplica** el rendimiento
   de cada trigger existente, no lo suma.

2. **Bodies ensayísticos sin wikilinks de verbos trigger-friendly**
   (deudas #2 Zeus, #3 Newton, #5 filosofía+historia)
   No se arregla con más triggers — requiere leer prosa
   semánticamente. Solución: **LLM-assisted extractor** que emite
   triples sin depender del patrón exacto.

3. **Clusters enteros bloqueados por MISSING_ENTITY** (deuda #4
   Einstein)
   No se arregla con más extracción — requiere **creación masiva
   de entidades** como campaña explícita, no one-off.

2.1 no puede resolver ninguno de los tres dentro de su alcance:
- Matcher regex: cambio de arquitectura del extractor, ~40-80 LoC
- LLM-assisted: nueva dependencia, nuevo pipeline, evaluación de
  calidad
- Cluster migration: decisión de qué crear y en qué orden; no es
  tarea de review humano por triple

Cada uno es un scope de campaña por sí solo.

## 7. Propuesta de enfoque para 2.2

### Objetivo principal

Eliminar los 3 cuellos de botella estructurales identificados en 2.1,
con la hipótesis: **si los tres se resuelven, un batch promedio sobre
el vault post-2.2 rendirá 5-15 edges en lugar de 1-3**.

### Subcampañas propuestas (orden sugerido)

#### 2.2A — Matcher regex-tolerante (deuda #6)

- Reemplazar el `str.find` del proposer por un motor regex que
  acepte inserciones limitadas entre tokens de triggers nominales.
- Patrón propuesto: convertir cada trigger multi-palabra `"X de"`
  en regex `r"X\s+(?:\w+\s+){0,2}de"` (0 a 2 palabras intermedias).
- Tests extensivos para cubrir los casos observados en 2.1:
  "sucesor reluctante de", "discípulo favorito de", "rival declarado
  de", etc.
- Coste estimado: 2-3 días. ROI: desbloquea docenas de casos ya
  observables en el vault.
- Riesgo: FPs nuevos por regex demasiado liberal. Mitigación:
  revisión cuidadosa de tests + batch regen sobre F2/Fase1/Fase2
  para medir.

#### 2.2B — LLM-assisted extractor (deudas #2, #3, #5)

- Arquitectura: el LLM lee el body completo de una nota, produce
  un proposal YAML **con el mismo formato que el pattern extractor**
  (evidence.source del enum cerrado, confidence high/medium,
  object_status, review_note). Es decir, el LLM alimenta el mismo
  pipeline de review/apply existente — no es un camino paralelo.
- Fallback y mezcla: el pattern extractor sigue corriendo primero;
  el LLM complementa cubriendo casos donde pattern emite 0.
- Coste estimado: 1-2 semanas (diseño del prompt, evaluación,
  calibración de confianza, integration tests).
- ROI: desbloquea Zeus, Newton, Averroes, Agustín, Parménides y
  todas las notas "ensayísticas" del vault.
- Riesgo: calidad del LLM, alucinaciones, tamaño de context. El
  protocolo de review humano por batch ya es la red de seguridad.

#### 2.2C — Einstein cluster + Newton Principia (deuda #4)

- Campaña dedicada que crea las 11 entidades faltantes de Einstein
  (Mileva Marić, Elsa Einstein, Marcel Grossmann, Max Planck, Niels
  Bohr, Arthur Eddington, Princeton, Ulm, ETH Zúrich, Instituto de
  Estudios Avanzados, Teoría de la relatividad, Efecto fotoeléctrico)
  más Principia Mathematica.
- Usa `brain create-entity` o direct-enrich en bloque.
- Después: batch "cluster-apply" que tipa todas las relaciones
  recién desbloqueadas en Einstein + Newton + otras notas afectadas.
- Coste estimado: 3-5 días (creación + review).
- ROI proyectado: ~25-40 typed edges nuevos en un solo push.

#### 2.2D (opcional) — Wikify pass selectivo + Kant fix

- Añadir wikilinks donde la prosa menciona entidades canónicas pero
  no las linkea ("escuela eleática" en Parménides, Claudio en
  Nerón's adoption sentence).
- Incluye fix del Kant body wikilink malo (deuda #1).
- Coste estimado: 2-3 días.
- ROI: desbloquea los triples que ni regex ni LLM pueden (wikilink
  ausente es pre-condición de extracción).

#### 2.2E (opcional) — `--preserve-reviews` flag

- Pequeña mejora del batch regen para preservar `status` y
  `review_note` matching por id de triple.
- Coste: ~20 LoC + tests.
- ROI: cero re-revisión cuando regeneramos batches tras mejoras
  del extractor.

### Success criteria propuestos para 2.2

- **Matcher regex** (2.2A): Tiberio desbloqueado; ≥5 triples
  nuevos detectados al regen F2 y Fase2-romanos.
- **LLM extractor** (2.2B): Zeus, Averroes, Agustín, Parménides
  producen ≥3 triples high-confidence cada uno tras review. Reject
  rate ≤40%.
- **Einstein cluster** (2.2C): Einstein alcanza ≥15 typed edges;
  Newton alcanza ≥5 nuevos.
- **Net typed edges añadidos en 2.2**: ≥150 (vs. 17 de 2.1).
- **High confidence ratio**: ≥85% (vs. 100% en 2.1 — tolerar un
  poco más de medium dado el LLM).
- **Body drift**: cero (mantener invariante).

### Qué NO debe hacerse en 2.2

- Forzar el objetivo numérico 400 de 2.1 — que murió con buen motivo.
- Añadir más triggers nominales individuales — no escalan aislados.
- Crear entidades one-by-one fuera de contexto — solo en bloques
  de cluster.
- Tocar body de notas para cambiar formato proposer-friendly —
  eso es authorship, no typing. Fuera de 2.x.

## 8. Navegación

- Format spec: [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md)
- Infraestructura base: [`CAMPAIGN_2_0_SUMMARY.md`](CAMPAIGN_2_0_SUMMARY.md)
- Deudas acumuladas: [`KNOWN_CLEANUP_DEBT.md`](KNOWN_CLEANUP_DEBT.md)
- Campañas estructurales previas:
  [`CAMPAIGN_0_SUMMARY.md`](CAMPAIGN_0_SUMMARY.md),
  [`CAMPAIGN_0_5_SUMMARY.md`](CAMPAIGN_0_5_SUMMARY.md),
  [`CAMPAIGN_1_OPERATIONS.md`](CAMPAIGN_1_OPERATIONS.md)
- Creation queue operativa: `<vault>/.brain-ops/relations-proposals/creation-queue.md`

## 9. Changelog

- **2026-04-19 (closure)** — Campaña 2.1 cerrada. 6 batches, 2
  mini-subfases, +17 typed edges, 920 tests, 6 deudas estructuradas.
  Cuello de botella identificado y documentado. Propuesta 2.2
  delineada en 4-5 subcampañas con success criteria cuantificados.
