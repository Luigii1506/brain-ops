# Campaña 2.2A — Summary

**Útil pero insuficiente.** 2.2A implementó el matcher regex-tolerante
propuesto en el cierre de 2.1, lo validó con un experimento decisorio
sobre 5 batches benchmark, y produjo un resultado honesto: la mejora
**aporta valor concreto** (1 TP real, 3 FP históricos eliminados por
word boundary) pero **no resuelve el cuello de botella principal**.
Los 3 FPs que emergieron del benchmark son todos casos de
**semántica modificada por adverbios/preposiciones/negaciones** —
precisamente la categoría que 2.2B LLM necesita atender.

La decisión formal fue capturar el TP real del experimento
(`Tiberio succeeded → Augusto`, +1 typed edge), preservar el código
del matcher regex (tiene residual útil), y abrir 2.2B como campaña
siguiente.

Ver [`CAMPAIGN_2_1_SUMMARY.md`](CAMPAIGN_2_1_SUMMARY.md) §7 para el
plan original donde 2.2A fue propuesto como experimento decisorio,
y [`KNOWN_CLEANUP_DEBT.md`](KNOWN_CLEANUP_DEBT.md) para las deudas
estructurales que motivan 2.2B.

---

## 1. Lo que 2.2A entregó

### Infraestructura

| Paso | Commit | Delivered |
|---|---|---|
| 1 | `486b7e1` | `_find_trigger_in_window` extraído como helper (zero behavior change) |
| 2 | `61db89f` | `_build_regex_for_trigger(phrase, max_intermediate)` función pura + `@lru_cache` + 7 tests unitarios |
| 3 | `64009d0` | Integración: dispatch en `_find_trigger_in_window` (multi-word → regex, single-word → str.rfind) + 4 integration tests |

Diseño del regex generado:
- Para trigger multi-palabra `"w1 w2 ... wK"`:
  `\bw1(?:\s+\w+){0,N}\s+w2(?:\s+\w+){0,N}\s+...wK\b` con N=2
- Word boundaries `\b` en ambos extremos → evita substring matches
- `\w+` estricto para tokens intermedios → puntuación corta cláusula
- `re.IGNORECASE` → acepta cualquier capitalización
- `@lru_cache` sobre `_build_regex_for_trigger` → amortiza compilación

### Benchmark ejecutado

5 batches regenerados con `--overwrite` contra backup `.pre-2.2A/`:

| Batch | Tipo | Pre | Post | Nuevos | Regresiones reales |
|---|---|---:|---:|---:|---:|
| F2-history | primario | 37 | 29 | 2 | 0 |
| Fase1-filosofos-nuevos | primario | 3 | 1 | 0 | 0 |
| Fase2-romanos-post-augusto | primario | 3 | 4 | 2 | 0 |
| F3-religion | control | 3 | 3 | 0 | 0 |
| F4-science | control | 1 | 1 | 0 | 0 |

**4 triples nuevos en primarios; 0 contaminación en controles.**

### Apply realizado

1 triple (el único TP) se aplicó al vault:

```
Tiberio  succeeded  Augusto   (high confidence)
```

Body byte-idéntico pre/post; cero drift fuera del manifest. SQLite
`entity_relations.predicate IS NOT NULL`: **88 → 89**.

## 2. Lo que funcionó

### Tiberio desbloqueado

El caso-prueba central. Body: *"Hijastro y **sucesor reluctante de**
[[Augusto]]"*. El adverbio "reluctante" intercalado entre "sucesor" y
"de" había bloqueado Tiberio en 2.1 (deuda #6 de
`KNOWN_CLEANUP_DEBT.md`). El matcher regex con tolerancia a 1 token
intermedio capturó el pattern y emitió el triple correctamente. Ahora
en SQLite.

### FPs previos eliminados por word boundary

Bonus inesperado: **3 FPs conocidos de Marco Aurelio que habíamos
rechazado en 2.1 dejaron de emitirse** tras 2.2A, no porque fueran
filtered por `already_typed` sino porque el nuevo regex aplica `\b`:

| FP eliminado | Razón |
|---|---|
| `Marco Aurelio born_in → Antonino Pío` | Trigger más cercano `adoptado por` (de mini-subfase #2) gana sobre `nacimiento en`; target ya típado como `adopted_by` → filtered |
| `Marco Aurelio ruled → Domiciano` | Old `str.rfind` encontraba `"emperador de"` dentro de `"emperador desde"` (substring no-word-boundary). Nuevo `\bde\b` rechaza correctamente. |
| `Marco Aurelio ruled → Tiberio` | Mismo bug del substring `desde`, eliminado por `\b` |

Los tres son **word-boundary bug fixes** que existían silenciosamente
en 2.1. El reviewer humano los había atrapado como rejected FPs, pero
ahora el extractor mismo los previene. Menos carga de review a futuro.

### Cero regresiones reales

Todas las 13 "regresiones" brutas del diff fueron clasificadas:
10 son `already_typed` (comportamiento correcto), 3 son los FP
eliminations mencionados arriba (mejora, no pérdida). **Cero triples
previamente aplicados perdidos.**

### Controles limpios

F3-religion y F4-science produjeron 0 nuevos triples post-2.2A. No
hay señal de over-matching. El matcher regex respetó los umbrales
(`_MAX_INTERMEDIATE_TOKENS = 2`) y las word boundaries previnieron
inflación.

### Test suite mantenida

934 tests pass, 12 skipped (920 pre-2.2A + 14 nuevos: 3 helper + 7
regex builder + 4 integration). Los tests existentes no requirieron
modificación — backwards compat preservada sobre todo el pipeline.

## 3. Lo que NO resolvió

3 de los 4 triples nuevos del benchmark fueron FPs — todos de la
misma categoría estructural: **adverbios/preposiciones/partículas
intercaladas que invierten la semántica del pattern**.

### FP #1 — modificador tipo-cambiante

`Augusto child_of → Julio César`

Body: *"Sobrino-nieto e **hijo adoptivo de** [[Julio César]]"*. El
adverbio "adoptivo" entre "hijo" y "de" cambia el tipo de relación
de biológica a adoptiva. Emitir `child_of` revertiría la distinción
adoptiva (`adopted_by`) establecida en Paso 1 de 2.1.

### FP #2 — negación no respetada

`Marco Aurelio appears_in → Meditaciones (Marco Aurelio)`

Body: *"atribución debatida, **no aparece** literalmente en las
[[Meditaciones]]"*. El matcher captura `aparece ... en` ignorando la
negación que antecede. Doble FP: predicado incorrecto (Marco Aurelio
es `author_of`, no `appears_in`) + negación colapsada.

### FP #3 — preposición-reversora

`Trajano ruled → Italia`

Body: *"Primer emperador **nacido fuera de** [[Italia]]"*. El matcher
captura `emperador ... de` cubriendo los 2 tokens "nacido fuera". La
preposición "fuera" invierte literalmente el significado: `nacido fuera
de` = opuesto de `emperador de`. Trajano era emperador del Imperio
Romano completo (nacido en Hispania), no gobernante de Italia.

### Patrón común

Los 3 FPs son casos donde **partículas funcionales dentro de la
ventana de tolerancia modifican o invierten la semántica del triple**.
Pattern matching — por tolerante que sea — no puede distinguir:

- `hijo adoptivo de` vs `hijo de` (tipo-cambiante)
- `no aparece en` vs `aparece en` (negación)
- `nacido fuera de` vs `emperador de` (preposición-reversora)

Ninguna ampliación adicional de triggers ni ajuste de
`_MAX_INTERMEDIATE_TOKENS` resuelve esto. Requiere **lectura semántica
del contexto**, no match sintáctico.

## 4. Métricas vs umbrales del plan

Plan original (§13 de 2.2A):

| Criterio | Umbral éxito | Umbral fracaso | Resultado |
|---|---|---|---|
| Nuevos canonical primarios | ≥ 10 | < 5 | **4** → bajo fracaso |
| TP rate sobre nuevos | ≥ 60% | < 40% | **25%** → bajo fracaso |
| Tiberio desbloqueado | requerido | — | ✓ |
| Regresiones reales | = 0 | > 0 | **0** ✓ |
| Controles con nuevos | ≤ 1 | ≥ 2 | **0** ✓ |

**Dos criterios cumplidos (Tiberio + regresiones + controles), dos
bajo el umbral de fracaso (volumen + TP rate)**. Per el árbol de
decisión del plan, esto activa **"matcher regex insuficiente → abrir
2.2B LLM"**.

## 5. Decisión tomada

**Opción B del reporte final** (el usuario eligió explícitamente):

- Aplicar el único TP real (Tiberio succeeded Augusto): +1 typed edge
- Rechazar los 3 FPs semánticos
- Cerrar 2.2A como "útil pero insuficiente"
- Abrir 2.2B LLM como siguiente campaña

Opción A (no aplicar nada) habría sido la lectura más estricta del
plan. Opción C (iteración de triggers adicionales) habría añadido
quizá 1-2 TPs más (`Tiberio adopted_by Augusto` vía `hijastro de`,
`Averroes influenced_by Aristóteles` vía `comentarista de`) **sin
reducir los FPs** — mismo cuello de botella semántico persistiría.

Opción B preserva el valor concreto del experimento sin diluir la
decisión estructural.

## 6. Deltas sobre el repo

### Código

- `src/brain_ops/domains/knowledge/relations_proposer.py` — matcher
  regex integrado. Delta ~60 LoC. **Se preserva** aunque 2.2B pueda
  obsoletar el pipeline pattern-based completo; el regex matcher
  sigue activo y reduce carga de review en batches futuros que
  contengan casos de adverbios/adjetivos intercalados.
- 14 tests nuevos (`MatcherHelperTestCase` 3 + `RegexBuilderTestCase` 7
  + `MatcherIntegrationTestCase` 4)

### Docs

- `docs/operations/CAMPAIGN_2_2A_SUMMARY.md` — este archivo
- `KNOWN_CLEANUP_DEBT.md` — deuda #6 (Tiberio exact-match insuficiente)
  queda **resuelta parcialmente** (Tiberio específico desbloqueado)
  pero **el patrón general de semántica modificada por partículas
  intercaladas persiste** como deuda nueva para 2.2B

### Vault

- +1 typed edge: `Tiberio succeeded Augusto`
- SQLite `entity_relations` (predicate IS NOT NULL): 88 → 89
- 0 body drift, 0 drift outside manifest
- Batch artifact: `<vault>/.brain-ops/relations-proposals/batch-2.2A-tiberio-tp/`
- Los 5 batches benchmark (F2, Fase1, Fase2, F3, F4) quedan restaurados
  a su estado 2.1-closure (pre-experimento)

## 7. Qué queda para 2.2B

La evidencia de 2.2A refina la propuesta original de 2.2B (§7.2 de
`CAMPAIGN_2_1_SUMMARY.md`):

**Scope confirmado como necesario**:
- Lectura semántica de prosa que el pattern matcher no puede hacer
- Respeto a negaciones ("no aparece", "nunca fue")
- Distinción de modificadores de tipo ("hijo adoptivo" vs "hijo")
- Detección de preposiciones-reversoras ("nacido fuera de")

**Ganancia marginal conocida del matcher regex** (ya incorporada, no
debe duplicarse en 2.2B):
- ~1 TP cada 5 batches de tamaño similar al benchmark
- Word-boundary cleanups incidentales
- Tolerancia a adverbios simples no-semánticos (caso Tiberio,
  probablemente ~5-10 casos similares en todo el vault)

**Hipótesis refinada para 2.2B**:
> "Un extractor LLM-asistido que lea la prosa semánticamente, respete
> negaciones y modificadores, y produzca proposals en el mismo formato
> YAML del pipeline existente, es el único camino para desbloquear
> >80 typed edges en el vault actual."

El orden de subcampañas propuesto en el cierre de 2.1
(2.2B → 2.2C cluster Einstein → 2.2D wikify) sigue siendo el
correcto; 2.2A confirmó que no hay atajos pattern-based.

## 8. Changelog

- **2026-04-19 (2.2A closure)** — Experimento decisorio completado.
  Decisión: matcher regex insuficiente pero residual útil; abrir
  2.2B LLM. Entregó +1 typed edge (Tiberio), +14 tests, 3 FP
  eliminations incidentales. Cerrado con tag `kg-campaign-2-2A-complete`.
