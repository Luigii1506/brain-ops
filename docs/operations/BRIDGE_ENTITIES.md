# Bridge Entities

Patrón para entidades que viven legítimamente en **más de un dominio** del
vault — filosofía y religión, ciencia y filosofía, historia y política,
etc. — sin que sea correcto reclasificarlas a uno solo.

## Por qué este doc existe

Las campañas de dominio (Religion, Ciencia, Filosofía) tienden a "tirar"
las entidades hacia su silo. Pero algunas figuras y obras pertenecen
genuinamente a varios dominios simultáneamente:

- **Confucio** es figura religiosa y filosófica
- **Marco Aurelio** es emperador (historia) y filósofo (filosofía)
- **Siddhartha Gautama** funda una religión y articula una filosofía
- **Pitágoras** es filósofo, matemático y figura mística
- **Tao Te Ching** es texto filosófico y texto religioso

Reclasificarlos a un único dominio destruye queries y backlinks. La
solución es tratarlos como **bridge entities** — entidades cuyo
frontmatter declara explícitamente la pertenencia múltiple.

## Patrón

### 1. `domain` como lista YAML

En lugar de:

```yaml
domain: filosofia
```

Usar:

```yaml
domain:
- filosofia
- religion
```

Esta sintaxis ya está establecida en el vault (ver `Marco Aurelio`,
`Pitágoras`, `Tales de Mileto`, `Euclides`).

### 2. Typed `relationships:` en lugar de rename

Si la nota nació en un dominio (ej: filosofía) y se descubre que también
pertenece a otro (ej: religión), **no** cambiar `type`, **no** renombrar
el archivo, **no** mover la nota. En su lugar, añadir typed
`relationships:` en frontmatter que la enlacen al grafo del nuevo
dominio:

```yaml
relationships:
- predicate: founder_of
  object: Confucianismo
  confidence: high
- predicate: associated_with
  object: Confucianismo
  confidence: high
```

### 3. Preservar el cuerpo y los backlinks existentes

- No reescribir secciones existentes
- No tocar `related:` legacy (el compilador los desduplica contra typed)
- No cambiar `subtype` salvo error claro
- No tocar `tags`, `field`, `epistemic_mode`

### 4. Casos donde NO aplica el patrón bridge

- **Notas-perspectiva**: si la nota es deliberadamente una lente
  específica (ej: `Budismo (filosófico)` es la perspectiva filosófica
  del budismo), **no añadir** religion al domain. Crear o usar la nota
  canónica del otro dominio (`Budismo`) y enlazar entre las dos vía
  `associated_with`.
- **Disambiguados**: si existen dos entidades distintas con bases
  semánticas distintas (`Ética` la disciplina vs `Ética (Spinoza)` el
  libro), preservar la separación, no fusionar.

## Distinción crítica — bridge vs perspectiva

| | Bridge entity | Perspective note |
|---|---|---|
| Domain | Lista (`[filosofia, religion]`) | Singular (la perspectiva) |
| Compite con canónica del otro dominio | No | Sí — y debe coexistir explícitamente |
| Ejemplo | `Confucio` (filosofía + religión simultáneas) | `Budismo (filosófico)` ⟷ `Budismo` |
| Relación entre las dos notas | N/A — es una sola nota | `associated_with` bidireccional, con `reason` que documenta la complementariedad |

## Workflow para añadir bridge a una nota existente

1. Confirmar que la nota cumple criterios de bridge (no es perspectiva)
2. **Frontmatter-only edit**: cambiar `domain: X` → `domain: [X, Y]`
3. Añadir bloque `relationships:` con typed edges al grafo del dominio
   nuevo (founder_of, uses_text, related_concept, etc.)
4. Si la nota incluye `## Relationships` inline en el cuerpo, no
   tocarla (queda como redundancia inofensiva; el compilador desduplica)
5. Post-step: `brain reconcile --skip-wikify --skip-cross-enrich`
   (body-safe — la edición fue frontmatter-only)
6. Verificar en SQLite que los nuevos edges ingestaron

## Workflow para crear nota perspectiva (no bridge)

Cuando la perspectiva específica merece nota propia y no debe colapsar
con la canónica:

1. Crear nota canónica del dominio principal (ej: `Budismo` con
   `type: religion`, `domain: religion`)
2. Crear (o preservar) nota perspectiva con sufijo disambiguador (ej:
   `Budismo (filosófico)` con `type: concept`, `domain: filosofia`,
   `subtype: school_of_thought`)
3. Añadir typed `associated_with` bidireccional con `reason` que
   documente la complementariedad:

   ```yaml
   # en Budismo (filosófico).md
   relationships:
   - predicate: associated_with
     object: Budismo
     confidence: high
     reason: Perspectiva filosófica complementaria del Budismo como religión
   ```

4. La nota canónica reciproca con el `associated_with` inverso

## Anti-patrones

### Renombrar la nota legacy

Mal: cambiar `Confucio.md` → `Confucio (filósofo).md` para "hacer sitio"
a `Confucio (religión).md`. Rompe ~30 backlinks y crea una distinción
artificial.

Bien: una sola nota `Confucio.md` con `domain: [filosofia, religion]`.

### Cambiar `type` para encajar en el otro dominio

Mal: cambiar `Confucianismo` de `type: concept` a `type: religion`.
Pierde `subtype: school_of_thought`, rompe queries por concept,
desestabiliza referencias.

Bien: preservar `type: concept`, ampliar `domain` a lista.

### Fusionar perspectiva con canónica

Mal: borrar `Budismo (filosófico)` y dejar sólo `Budismo`. Pierde la
articulación filosófica densa que ya estaba escrita.

Bien: dos notas, una perspectiva una canónica, cross-linked vía
`associated_with` con `reason` explícito.

## Evidencia empírica — Campaña 3 reclasificación

Seis figuras/obras reclasificadas como bridge:

| Nota | Antes | Después | Estrategia |
|---|---|---|---|
| Confucianismo | concept / filosofia | concept / [filosofia, religion] | Bridge |
| Taoísmo | concept / filosofia | concept / [filosofia, religion] | Bridge |
| Confucio | person / filosofia | person / [filosofia, religion] | Bridge |
| Lao Tsé | person / filosofia | person / [filosofia, religion] | Bridge |
| Siddhartha Gautama | person / filosofia | person / [filosofia, religion] | Bridge |
| Budismo (filosófico) | concept / filosofia | (sin cambio en domain) | Perspective — preservada |

Resultado: 16/16 typed edges nuevos ingestaron en SQLite, cero deletes,
cero renames, cero rewrites de cuerpo, queries por `domain: religion`
ahora alcanzan a las 5 bridge entities, queries por `domain: filosofia`
siguen funcionando intactas.

## Ver también

- [`SCHEMA_GOVERNANCE.md`](SCHEMA_GOVERNANCE.md) — extensión de
  `CANONICAL_PREDICATES` y `ENTITY_TYPES` cuando el bridge requiere
  predicados nuevos
- [`RELATIONS_FORMAT.md`](RELATIONS_FORMAT.md) — formato del bloque
  `relationships:` en frontmatter
- [`NAMING_RULES.md`](NAMING_RULES.md) — convenciones de naming y
  disambiguación
