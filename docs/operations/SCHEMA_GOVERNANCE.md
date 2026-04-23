# Schema Governance

Cuándo y cómo extender el vocabulario canónico del compilador
(`CANONICAL_PREDICATES`, `ENTITY_TYPES`, `ENTITY_SCHEMAS`) sin romper
backward compatibility ni introducir degradación semántica.

## Por qué este doc existe

Las campañas eventualmente requieren predicados o tipos de entidad que
el vocabulario canónico actual no soporta. La tentación es **degradar
semántica** mediante aliasing arbitrario (ej: `uses_text → associated_with`,
`branch_of → part_of`). Esa decisión silenciosa colapsa información
queryable y degrada el grafo permanentemente.

La política correcta es **extender el vocabulario canónico de manera
aditiva** cuando el caso lo justifica.

## Tres registros que viven en lockstep

El compilador a SQLite valida contra tres registros que deben mantenerse
sincronizados:

1. **`CANONICAL_PREDICATES`** en
   [`src/brain_ops/domains/knowledge/object_model.py`](../../src/brain_ops/domains/knowledge/object_model.py)
   — dict `predicate → descripción`. El parser
   `relations_typed.parse_relationships` rechaza silenciosamente
   cualquier predicado que no esté aquí.
2. **`ENTITY_TYPES`** en
   [`src/brain_ops/domains/knowledge/entities.py`](../../src/brain_ops/domains/knowledge/entities.py)
   — dict `type → descripción`. El compilador descarta entidades cuyo
   `type` no esté aquí (incluso si `entity: true` y `name` están).
3. **`ENTITY_SCHEMAS`** en el mismo archivo — dict `type → EntitySchema`.
   Contiene `required_fields`, `optional_fields`, `sections`. El test
   `test_entity_schemas_exist_for_all_types` exige que cada entrada de
   `ENTITY_TYPES` tenga su `ENTITY_SCHEMAS` correspondiente.

Tocar uno sin tocar los otros **rompe tests** o **rompe ingestión
silenciosamente**.

## Cuándo extender

Antes de añadir un predicado o tipo nuevo, verificar:

- ¿El concepto **no es expresable** sin pérdida semántica con el
  vocabulario actual? (no aceptar respuestas tipo "se aproxima con X")
- ¿Va a usarse en **al menos un dominio completo** del vault? (no añadir
  predicados de un solo uso)
- ¿La adición es **aditiva**? (los predicados existentes siguen
  funcionando, ningún path existente se rompe)
- ¿La spec de la campaña que motiva la extensión es **explícita** sobre
  el vocabulario? (extensiones ad-hoc tienden a deuda)

## Cómo extender — checklist

### 1. Predicados nuevos

- Añadir entradas a `CANONICAL_PREDICATES` agrupadas en una sección
  comentada (`# Religion structural — Campaña 2`)
- Añadir aliases español/inglés a `PREDICATE_NORMALIZATION` para que el
  extractor LLM los normalice (`"founded by": "founded_by"`,
  `"fundado por": "founded_by"`)
- Añadir test en `tests/test_relations_typed_parser.py` que verifique
  ingestión de cada predicado nuevo (tres tests recomendados:
  `test_all_<X>_predicates_accepted`, `test_<X>_predicates_in_canonical_dict`,
  `test_<X>_predicate_with_confidence_and_reason`)
- Correr `python -m unittest discover tests` antes de continuar

### 2. Tipos de entidad nuevos

- Añadir entrada a `ENTITY_TYPES` con descripción 1-línea
- Añadir entrada **simultánea** a `ENTITY_SCHEMAS` con `required_fields`,
  `optional_fields`, `sections=_STANDARD_SECTIONS`
- Si las notas existentes con ese type carecen de `entity: true` y
  `name`, escribir un script de patch frontmatter-only para añadirlos
  (no borrar otros campos)
- Correr el test suite

### 3. Verificación post-cambio

```bash
source .venv/bin/activate
python -m unittest discover tests
brain reconcile --skip-wikify --skip-cross-enrich --config config/vault.yaml
python -c "
import sqlite3, pathlib
db = pathlib.Path('<vault>/.brain-ops/knowledge.db')
con = sqlite3.connect(db); c = con.cursor()
new_preds = ('<pred1>','<pred2>','...')
c.execute(f\"SELECT predicate, COUNT(*) FROM entity_relations WHERE predicate IN ({','.join('?'*len(new_preds))}) GROUP BY predicate\", new_preds)
for row in c.fetchall(): print(row)
"
```

Si las cuentas son cero, el grafo no ingestó y la extensión está
incompleta.

## Anti-patrones

### Aliasing semántico arbitrario

Mal:

```python
# en migration script
PREDICATE_REMAP = {
    "founded_by": "associated_with",  # pierde la dirección fundacional
    "branch_of": "part_of",           # pierde la jerarquía taxonómica
    "celebrated_by": "practiced_by",  # pierde la dimensión festiva
}
```

Bien: añadir los predicados al canon.

### Cambiar `type` de notas existentes en lugar de extender `ENTITY_TYPES`

Mal: renombrar masivamente `type: religion` → `type: concept` para que
el compilador acepte las notas.

Bien: añadir `religion` a `ENTITY_TYPES` + `ENTITY_SCHEMAS`. Las notas
preservan su clasificación semántica.

### Tocar un registro sin los otros

Mal: añadir `religion` a `ENTITY_TYPES` y olvidar `ENTITY_SCHEMAS`. El
test `test_entity_schemas_exist_for_all_types` revienta.

Bien: lockstep siempre. Idealmente en el mismo commit.

## Evidencia empírica — Campaña 2 governance

La sesión que motivó este doc añadió:

- **12 predicados** a `CANONICAL_PREDICATES` (founded_by, founder_of,
  uses_text, text_of, has_branch, branch_of, celebrates, celebrated_by,
  practiced_in, related_concept, contrasts_with, emerged_in)
- **5 tipos** a `ENTITY_TYPES` (religion, text, institution, practice,
  festival) + 5 entradas correspondientes en `ENTITY_SCHEMAS`
- **3 tests nuevos** en `test_relations_typed_parser.py`
- **24 aliases** en `PREDICATE_NORMALIZATION`

Resultado: 206 edges religion-domain previamente rechazados se
ingestaron en SQLite. Cero cambios destructivos. Test suite pasó
1070/1070.

## Ver también

- [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md) — formato del bloque
  `relationships:` en frontmatter
- [`CAMPAIGN_2_0_SUMMARY.md`](CAMPAIGN_2_0_SUMMARY.md) — origen del
  sistema de typed relations
- [`MIGRATIONS.md`](MIGRATIONS.md) — reglas de migración del schema
  SQLite (no aplican a extensiones de vocabulario, sólo a cambios de
  tabla)
