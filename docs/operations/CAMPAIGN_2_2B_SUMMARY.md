# Campaña 2.2B — Summary

**Mejora material, cierre pragmático.** 2.2B añadió un extractor LLM-assistido
sobre el pipeline de 2.1 para resolver la categoría de falsos positivos
semánticos que 2.2A no podía atender (negaciones, preposiciones reversoras,
adopción vs filiación, etc.). El extractor pasó por tres iteraciones de
ajuste guiadas por un golden set de 10 fixtures y un benchmark sobre 8+10
notas reales del vault. Al final, el sistema:

- cruza el umbral de green-light del golden set con margen (composite
  0.8095, umbral 0.65),
- reduce materialmente los dos patrones sistémicos detectados
  (inversiones de direccionalidad `influenced/_by` y alucinaciones de
  `adopted_by`),
- mantiene **mnp_rate = 1.00** en el golden set (cero violaciones
  controladas),
- deja un patrón residual de alcance muy pequeño — un único caso de
  `adopted_by` alucinado que pasa el marker léxico por colisión con
  contexto teológico no relacionado, confidence=medium, rationale
  auto-confesional — aceptable para operación human-in-the-loop.

La decisión formal fue **cerrar 2.2B aquí**: el patrón residual no
justifica la complejidad adicional de extender Check 9 a proximidad
objeto-marker, y la relación costo-beneficio de seguir puliendo es
peor que capturar el progreso logrado y avanzar al uso real.

Ver [`CAMPAIGN_2_2A_SUMMARY.md`](CAMPAIGN_2_2A_SUMMARY.md) para la
motivación (2.2A validó que el resto de FPs son semánticos y requieren
LLM) y [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md) para el formato
de los proposals que este extractor genera.

---

## 1. Lo que 2.2B entregó

### Infraestructura (Pasos 1–6.5)

| Paso | Commit | Delivered |
|---|---|---|
| 1 | `...` | Schema + validator con checks 1–8 + stub (`propose_triples_via_llm`) |
| 2 | `...` | Prompt builder para `strict` y `deep` + formato JSON de salida |
| 3 | `...` | `AnthropicLLMClient` con retry / cache / test-seam |
| 4 | `...` | Merge con pattern extractor + source tagging (`["body"]`, `["llm"]`, `["body","llm"]`) |
| 5 | `...` | CLI flags `--mode {cheap,strict,deep}` + `--cache-dir` en `propose-relations` y `batch-propose-relations` |
| 6 | `9b2d58a` | Golden set de 10 fixtures + runner (`llm_golden_set.py`) + 18 tests |
| 6.5 | `af074b2` | `OpenAILLMClient` como hermano de Anthropic (default switch) + preflight OPENAI_API_KEY + smoke test |

### Iteraciones de ajuste (Pasos 7a–7d)

| Paso | Commit | Fix | Efecto |
|---|---|---|---|
| 7a.1 | `8502893` | **Fix 1**: validator whitespace-flexible (`_normalize_ws` colapsa `\s+` a espacio único en ambos lados del quote check) | Desbloqueó 4 fixtures que fallaban por line-wrapping YAML |
| 7a.1 | `8502893` | **Fix 2**: prompt tightening — "predicates vs flags" con 2 ejemplos positivos/negativos | Eliminó `predicate=tutored` y `predicate=hijastro_step_relation` del output del LLM |
| 7c | `<este commit>` | **Fix 3**: validator wikilink-stripping (`[[Target]]` y `[[Target\|Display]]` normalizados a display text antes del quote check) | Desbloqueó casos donde el LLM cita visualmente "sin" los brackets |
| 7c | `<este commit>` | **Fix 4**: prompt endurecido con reglas explícitas — direccionalidad `influenced/_by` (voz pasiva → `influenced_by`) y uso restrictivo de `adopted_by` (solo con marker adoptivo literal) | Inversiones de direccionalidad ÷3 (37.5% → 11.8%) |
| 7d | `<este commit>` | **Check 9**: gate determinista en validator para `adopted_by` — rechaza si body carece de marker adoptivo léxico (`adoptado`, `adoptiva`, `adopción`, `adopted`, `adoption`) | Halluc de `adopted_by` −75% (4 → 1) |

### Tests

- **1053 tests verdes** al cierre (1035 baseline 2.2A + 18 nuevos para 2.2B).
- 10 tests dedicados a Check 9 (`AdoptedByGateTestCase`) cubren: markers ES/EN, escape hatch del flag, no-interferencia con otros predicates, case-insensitive.

### Prompt version

- `PROMPT_VERSION = "v1.2"` — el cambio textual invalida el cache por hash
  de prompt (`LLMResponseCache`), así que cualquier re-corrida post-fix
  no contamina con respuestas viejas.

---

## 2. Métricas de impacto

### Golden set (10 fixtures, `gpt-4o-mini`, strict)

| Métrica | 7a inicial | 7a.1 | 7c | 7d (cierre) |
|---|---|---|---|---|
| `composite_score` | 0.2714 | 0.6786 | **0.8095** | 0.8095 |
| `overall_must_catch_rate` | 0.2857 (6/21) | 0.7143 (15/21) | **0.8095 (17/21)** | 0.8095 |
| `overall_must_not_propose_rate` | 0.9500 (19/20) | 0.9500 (19/20) | **1.0000 (20/20)** | 1.0000 |
| `overall_policy_pass_rate` | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Cruzó el umbral de green-light (≥ 0.65) en 7a.1 y se mantuvo estable en 7d.

### Benchmark vault (10 notas en 7b, 8 notas en 7c/7d subset)

**FOCO 1 — Direccionalidad `influenced` / `influenced_by`:**

| | 7b (antes) | 7c/7d (después) |
|---|---|---|
| Inversiones claras | 3 de 8 (37.5%) | **2 de 17 (11.8%)** |
| Reducción absoluta | — | **−33%** (a pesar de 2× volumen de influences emitidas) |
| Casos clave resueltos | Newton→Galileo ✅, Newton→Kepler ✅ | Aristóteles→Platón en dirección correcta ✅, Averroes←Al-Ghazali ✅ |
| Residuales | — | Agustín→Platón (invertido), Averroes→Aristóteles (invertido). El rationale del modelo admite la dirección correcta en prosa pero emite el predicate activo. |

**FOCO 3 — `adopted_by`:**

| | 7b (antes) | 7c (prompt) | 7d (Check 9) |
|---|---|---|---|
| `adopted_by` emitidos | 5 | 4 | **2** |
| Correctos | 1 (Tiberio) | 1 | 1 |
| Hallucinados | 4 | 3 | **1** |
| Halluc rate | 80% | 75% | **50%** |
| Rechazos `adopted_by_missing_marker` | 0 | 0 | **2** (Aristóteles→Filipo II, Tomás→Orden Predicadores) |

Reducción absoluta de halluc: **4 → 1 (−75%)**.

**FOCO 2 — Disambiguación de obras:**

No se intervino. 0 proposals con `object_status = DISAMBIGUATION_PAGE`
en la muestra — el modelo tiende a emitir el display text sin el
suffix de disambig (ej. `"Metafísica"` en vez de `"Metafísica
(Aristóteles)"`). Esto es deuda reconocida para una campaña futura.

### Costo operativo

| Componente | Costo |
|---|---|
| Golden set corrida 7a (10 fixtures, v1.0 prompt) | $0.0037 |
| Golden set corrida 7a.1 (v1.1 prompt + Fix 1/2) | $0.0050 |
| Benchmark vault 7b (10 notas, v1.1 prompt) | $0.0128 |
| Golden set corrida 7c (v1.2 prompt) | $0.0068 |
| Benchmark subset 7c (8 notas) | $0.0110 |
| Golden set 7d + benchmark 7d (cache hit total) | $0.0000 |
| **Total 2.2B pasos 7a–7d** | **~$0.039** |

El costo proyectado para correr `strict` sobre el vault completo (1048
entidades) es **~$1.34**. `deep` costaría aproximadamente 5× más por el
cap mayor de body y temperature > 0.

---

## 3. Patrones residuales (documentados, no resueltos)

### 3.1. Inversión ocasional de `influenced` / `influenced_by`

**Síntoma:** el modelo emite `influenced → X` con rationale que
literalmente dice "fue influenciado por X" (voz pasiva).

**Frecuencia observada:** 11.8% de los `influenced/_by` emitidos
(2/17) en la muestra post-7c.

**Por qué persiste:** el prompt v1.2 incluye 3 ejemplos con voz pasiva
y una regla explícita, pero `gpt-4o-mini` ocasionalmente auto-parafrasea
la oración en voz activa antes de emitir el predicate.

**Mitigación operativa:** el reviewer humano detecta la inversión en
~5 segundos leyendo el rationale; la fecha de nacimiento/muerte de las
entidades suele hacer obvia la dirección correcta. No bloquea el uso
del pipeline.

**Ruta futura (si justifica):** Check 10 — gate direccional contra
signals temporales (fechas de nacimiento/muerte) del frontmatter, o
contra una cache de "predecesor/sucesor" derivada del vault. Complejidad
moderada, ROI a validar con más muestra.

### 3.2. `adopted_by` residual con marker léxico global

**Síntoma:** un caso en la muestra (Agustín → Mónica). El body de
Agustín contiene `"adoptada"` pero en contexto teológico no relacionado
(`"esta posición fue adoptada como ortodoxa"`), a ~3000 chars del
mention de Mónica. Check 9 lo acepta porque el marker existe en el body.

**Frecuencia observada:** 1 de 2 `adopted_by` emitidos post-Check 9
(50%) — pero también: 1 de los 8 notes benchmarked (12.5%).

**Por qué persiste:** Check 9 es marker-global; no verifica proximidad
objeto–marker.

**Mitigación operativa:** el rationale del modelo en este caso dice
literalmente *"la relación de adopción se infiere y no se afirma
explícitamente"* — el reviewer tiene señal auto-confesional clara.
confidence=medium fuerza `status: needs-refinement`, así que llega al
reviewer antes del apply, no al grafo.

**Ruta futura (si justifica):** extender Check 9 a proximidad —
verificar que el marker adoptivo aparezca dentro de ±N chars (N≈150–300)
del mention textual del object. Requiere resolver aliasado (wikilinks,
display names, nombres plurales). Coste: ~40 LoC + 5 tests.

### 3.3. Disambiguación de obras

**Síntoma:** 0 `DISAMBIGUATION_PAGE` emitidos en la muestra. El modelo
propone objects con display text (`"Metafísica"`, `"Ética"`) sin el
suffix de disambig que existe en el vault (`"Metafísica (Aristóteles)"`,
`"Ética (Spinoza)"`).

**Mitigación operativa:** los proposals salen con `object_status =
MISSING_ENTITY`, lo cual el reviewer ve explícitamente. Si el reviewer
sabe que existe la página con disambig, puede editar el object antes
de aprobar.

**Ruta futura:** enriquecer el prompt con una lista de páginas con
disambig en el vault (candidate_targets con el suffix), o post-proc
que detecte coincidencias de display-text y ofrezca el disambig.
Campaña 2.3 o posterior.

---

## 4. Por qué se decidió cerrar aquí

### Criterio operativo (del usuario)

> *"si el patrón residual de adopted_by cae claramente, cerramos 2.2B
> inmediatamente"*

Cayó claramente: **4 → 1 hallucinations (−75%)**.

### Criterio de robustez

- Golden set composite 0.81 (sobre umbral 0.65 con margen de +0.16).
- `mnp_rate = 1.00` en fixtures controladas.
- Direccionalidad ÷3.
- Costo operativo marginal ($1.34 para vault completo).
- 1053 tests verdes, cero regresiones.

### Criterio de no sobre-ajuste

Las 3 iteraciones (Fix 1+2 → Fix 3+4 → Check 9) corrigieron clases de
error, no fixtures específicos. Cada fix estuvo motivado por el análisis
honesto de fallos observados; ninguno fue tuning al golden set. El
golden set se mantuvo estable en 0.81 entre 7c y 7d: no fue "ganado"
por el último fix, solo robustecido.

### Criterio de ROI diminishing

Las rutas futuras documentadas (§3) son posibles pero tienen costo
incremental mayor que el beneficio marginal:

- Check 10 direccional requiere diseño dedicado y tiene riesgo de
  falso rechazo legítimo (ej. influencias bidireccionales).
- Proximidad en Check 9 requiere parsear objects en body (wikilinks,
  alias, plurales) — mucho código para un caso en la muestra.
- Disambig de obras tiene gran alcance pero merece su propia campaña.

La conclusión honesta: **2.2B mejoró materialmente el extractor. No
quedó perfecto. Pero ya quedó suficientemente robusto para uso real
con reviewer humano.** Eso era el objetivo.

---

## 5. Contrato con el resto del sistema

### Invariantes mantenidas

- **Cheap mode** (default CLI) preserva 2.2A exactamente: pattern
  extractor, cero llamadas al LLM, cero costo. El pipeline existente
  no se rompe.
- **Frontmatter-only apply** sigue siendo el único modo de escritura
  al vault. Check 9 actúa sobre el validator, no sobre el writer.
- **Human review mandatory**: todo proposal `medium` entra como
  `status: needs-refinement` y requiere aprobación antes de `apply`.
- **Source tagging**: cada `ProposedRelation` lleva `evidence_source
  = ["body"]`, `["llm"]`, o `["body","llm"]` (convergencia), visible
  en el YAML de propuestas.

### Breaking changes respecto a 2.2A

- Ninguno en APIs públicas. `propose_relations_for_entity` y
  `build_batch` añadieron parámetros `mode`, `llm_client`, `cache_dir`
  con defaults compatibles.
- El comportamiento default (`mode="cheap"`) es idéntico a 2.2A.

### Dependencias nuevas

- `openai ≥ 2.0` (instalado en el `.venv` del proyecto). Anthropic SDK
  sigue disponible vía `AnthropicLLMClient` si el usuario lo inyecta
  explícitamente.
- Ninguna migración de schema. `knowledge.db` intacta.

---

## 6. Recomendación de uso

**Para operación diaria:**

```bash
# Default: pattern extractor sin LLM (0 costo).
brain propose-relations "Entity Name" --config config/vault.yaml

# Strict LLM: añade proposals con cita literal.
brain propose-relations "Entity Name" --mode strict \
    --cache-dir .brain-ops/llm-cache/ --config config/vault.yaml

# Deep LLM: permite inferencias contextuales con medium + flag.
brain propose-relations "Entity Name" --mode deep --config config/vault.yaml
```

**Flujo completo:**

```
propose → review (humano edita YAML) → apply
```

Los campos `source` y `note` en el YAML son la señal principal para el
reviewer:

- `source: [body]` → detectado por regex 2.2A (alta precisión típica).
- `source: [llm]` → detectado solo por el LLM (revisar con más cuidado).
- `source: [body, llm]` → convergencia (máxima confianza).

**Patrones a revisar manualmente con atención** (deuda conocida):

1. Todo `influenced` / `influenced_by` cuando el object es una entidad
   de época muy distinta a la del sujeto — posible inversión.
2. Todo `adopted_by` con `confidence: medium` + flag
   `hijastro_step_relation` — leer el rationale; si dice "se infiere",
   revisar el body manualmente.
3. Objects con display text "corto" que pueden ser páginas con
   disambig (ej. `"Ética"`, `"Metafísica"`, `"República"`) —
   chequear si existe la versión con suffix en el vault.

---

## 7. Próximo paso lógico

El siguiente cuello de botella observado en el benchmark **no** es el
extractor, sino la **población del vault**:

- 48% de proposals aceptadas tuvieron `object_status = MISSING_ENTITY`.
- Esto significa que el pipeline identifica correctamente gaps de
  cobertura — y es una señal valiosa para priorizar qué entidades
  crear next.

Una campaña 2.3 natural sería "gap-driven entity creation": leer las
proposals LLM generadas sobre el vault actual, extraer los
`MISSING_ENTITY` de mayor frecuencia o mayor centralidad, y sembrar
entidades canónicas para que el siguiente batch de proposals convierta
esos gaps en typed edges completos.

Campaña 2.3 también puede abordar la deuda de disambig de obras (§3.3).

---

## 8. Referencias

- Golden set fixtures: `tests/fixtures/golden_set/*.yaml`
- Runner: `src/brain_ops/domains/knowledge/llm_golden_set.py`
- Validator + prompt + clients: `src/brain_ops/domains/knowledge/llm_extractor.py`
- Merge logic + CLI wiring: `src/brain_ops/domains/knowledge/relations_proposer.py`
- Docs previos: `CAMPAIGN_2_2A_SUMMARY.md`, `CAMPAIGN_2_1_SUMMARY.md`,
  `CAMPAIGN_2_0_SUMMARY.md`, `RELATIONS_FORMAT.md`.

**Tag de cierre:** `kg-campaign-2-2B-complete`.
