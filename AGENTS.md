# AGENTS.md — brain-ops

Contexto operativo para cualquier agente de IA que trabaje en este proyecto.

## Antes de iniciar CUALQUIER tarea

1. Ejecuta este comando y lee la salida:
```bash
brain session brain-ops --context-only --config config/vault.yaml
```
2. Esto te da: estado actual, proximas acciones, blockers, decisiones recientes, comandos
3. NO le pidas al usuario que re-explique el proyecto. El contexto esta en el sistema.

## Despues de completar trabajo significativo

Registra lo que hiciste:
```bash
brain project-log brain-ops "lo que hiciste" --config config/vault.yaml
brain refresh-project brain-ops --config config/vault.yaml
```

Usa prefijos para clasificacion:
- `"decision: usar X por Y"` → guardado en Decisions.md + registry
- `"bug: descripcion"` → guardado en Debugging.md
- `"next: lo que sigue"` → guardado en registry como pendiente

## Despues de commits en git

Los commits se registran automaticamente via el hook compartido del repo (`.githooks/post-commit`), que ejecuta `brain project-log` y `brain refresh-project`. Ademas, `.githooks/post-merge` y `.githooks/post-rewrite` corren `brain refresh-project` para resync del context pack cuando cambia el estado del repo sin un commit normal. Solo ejecuta `brain project-log` manualmente si el cambio involucra una decision arquitectonica o es particularmente significativo; despues corre `brain refresh-project` para mantener el context pack y el registry sincronizados.

## Resumen del proyecto

**brain-ops** es una estacion de inteligencia personal — un sistema operativo local-first que combina:
- **Obsidian vault** para entidades de conocimiento y notas reflexivas
- **SQLite** para datos estructurados de life-ops (dieta, fitness, gastos, habitos)
- **LLM multi-provider** (Ollama, OpenAI, Claude, DeepSeek, Gemini)
- **CLI-first** via Typer + Rich

## Stack

Python, Typer, Pydantic, SQLite, FastAPI (opcional), Rich

## Comandos clave

```bash
# Ejecutar tests
python -m pytest tests/ -x -q

# Info del sistema
brain info --config config/vault.yaml

# Operaciones de conocimiento
brain create-entity "Nombre" --type person --config config/vault.yaml
brain enrich-entity "Nombre" --url "..." --llm-provider openai --config config/vault.yaml
brain full-enrich "Nombre" --url "..." --config config/vault.yaml
brain check-coverage "Nombre" --config config/vault.yaml
brain reconcile --config config/vault.yaml
brain post-process "Nombre" --source-url "..." --config config/vault.yaml

# Operaciones personales
brain capture "texto en lenguaje natural"
brain daily-review --config config/vault.yaml
brain week-review --config config/vault.yaml

# Operaciones de proyecto
brain session brain-ops --config config/vault.yaml
brain project-log brain-ops "texto de update" --config config/vault.yaml
brain audit-project brain-ops --config config/vault.yaml
```

## Arquitectura (referencia rapida)

```
Interfaces (CLI, API, OpenClaw)
    ↓
Application (workflows)
    ↓
Domains (logica de negocio: knowledge, personal, projects, monitoring)
    ↓
Storage (SQLite + Obsidian vault + JSON registries)
```

- **SQLite** = fuente de verdad para datos operacionales (comidas, workouts, gastos, project logs)
- **Obsidian** = fuente de verdad para entidades de conocimiento, reflexiones, documentacion de proyectos
- **Registry JSON** = indice ligero (entity registry, project registry)
- **Config**: `config/vault.yaml`
- **Ruta del vault**: `/Users/luisencinas/Documents/Obsidian Vault`

---

## Reglas de operaciones de conocimiento

### Prioridad: siempre preferir comandos oficiales

Ver tambien: `docs/operations/AGENT_DIRECT_LLM_WORKFLOWS.md` para templates reutilizables y equivalencias entre pipeline oficial y workflows sin API usando Claude/Codex como LLM.

1. **USAR COMANDO OFICIAL** si existe (`brain create-entity`, `brain enrich-entity`, etc.)
2. **Escribir directamente + post-procesamiento** solo si no existe un comando para la tarea
3. **NUNCA editar una nota y abandonarla** — siempre ejecutar reconciliacion despues de ediciones directas

### Cuando se usan comandos oficiales (preferido):

```bash
# Crear entidad (usa frontmatter correcto, secciones por subtipo, compila)
brain create-entity "Nombre" --type person --config config/vault.yaml

# Enriquecer desde URL (usa source strategy, chunking, extraccion, cross-enrichment)
brain enrich-entity "Nombre" --url "https://..." --llm-provider openai --config config/vault.yaml

# Ingestar fuente (crea nota de fuente + actualiza registry + guarda JSON de extraccion)
brain ingest-source --url "https://..." --use-llm --config config/vault.yaml

# Query SIN LLM (registra query, detecta gaps, incrementa query_count — $0)
brain query-knowledge "pregunta" --config config/vault.yaml

# Query CON LLM (lo mismo + respuesta sintetizada — cuesta API)
brain query-knowledge "pregunta" --llm-provider openai --config config/vault.yaml

# Post-procesar despues de escribir directamente (emite evento, source note, extraction log, registry, compile)
brain post-process "Nombre Entidad" --source-url "https://..." --config config/vault.yaml

# Reconciliar todas las ediciones directas de una vez (registry sync + compile)
brain reconcile --config config/vault.yaml

# Auditoria
brain audit-knowledge --config config/vault.yaml

# Sugerencias
brain suggest-entities --config config/vault.yaml
```

---

## Cuando el agente escribe directamente (como LLM)

Esto se permite cuando el usuario dice "enriquece X" o "crea entidad X" en la conversacion.
El agente actua como el LLM directamente (sin costo de API). Pero DEBE seguir estas reglas:

### ANTES de escribir — determinar modo:

**DEEP MODE** (person, empire, civilization, battle, war, country, book, discipline):
1. Ejecutar `brain plan-direct-enrich "Nombre Entidad" --url "https://..." --config config/vault.yaml`
2. Usar el raw y el plan generado en `.brain-ops/direct-enrich/<slug>.json`
3. Escribir por pasadas cubriendo TODAS las secciones de alta prioridad y las de media prioridad valiosas
4. Despues de escribir, ejecutar `brain post-process ...` y `brain check-coverage ...`
5. Si coverage muestra gaps importantes, hacer otra pasada directa enfocada y volver a correr `post-process`

**LIGHT MODE** (ciudades, conceptos simples, animales, entidades menores):
1. WebFetch o usar conocimiento general
2. Escribir una nota solida cubriendo lo esencial
3. No se necesita verificacion formal de cobertura

### Regla: "Si la fuente lo tiene Y es estructuralmente importante, la nota lo cubre."

No TODAS las secciones — solo las importantes. Referencias, bibliografia, metadata = skip.
Campanas, puntos de inflexion, muerte, legado = siempre cubrir.

### Checklist para entidades DEEP MODE:
- ¿Estan TODAS las campanas/eventos principales cubiertos? (no solo los famosos)
- ¿Estan explicados los puntos de inflexion clave? (no solo listados como fechas)
- ¿Estan descritas las relaciones importantes con contexto?
- ¿Estan incluidas las decisiones estrategicas y sus consecuencias?
- ¿Estan anotadas las contradicciones e incertidumbres?
- ¿Entenderia un lector POR QUE esta entidad importa?

### Mientras escribe cualquier nota de entidad directamente:
1. Actualizar el campo `related` del frontmatter con todas las entidades mencionadas
2. Usar secciones especificas del subtipo de `object_model.py`
3. Usar predicados canonicos de `object_model.py` para relaciones
4. Siempre usar `[[wikilinks]]` para entidades mencionadas
5. Nunca dejar la seccion Identity vacia
6. Escribir en espanol
7. **SIEMPRE incluir `## Preguntas de recuperación`** con 5 preguntas:
   - 🟢 Recordar (1): dato concreto, fecha, nombre
   - 🟡 Explicar (2): por qué, cómo, causa-efecto
   - 🔴 Comparar (1): similitud/diferencia con otra entidad
   - ⚫ Aplicar (1): lección, patrón, transferencia
   Formato: `- 🟢 **¿Pregunta?** → Respuesta concreta`

### Despues de escribir, verificar cobertura:
```bash
brain post-process "Nombre Entidad" --source-url "https://url-usada" --config config/vault.yaml
brain check-coverage "Nombre Entidad" --config config/vault.yaml
```
Si check-coverage muestra gaps de alta prioridad, enriquecer esas secciones antes de continuar.

### Despues de verificar, cerrar el pipeline:
```bash
brain post-process "Nombre Entidad" --source-url "https://url-usada" --config config/vault.yaml
```
Este unico comando hace todo: emite evento, crea nota de fuente, guarda registro de extraccion, sincroniza registry, y compila a SQLite.

Si se editaron multiples entidades, ejecutar `brain reconcile` en su lugar (sincronizacion bulk sin trazabilidad por entidad).

### Para fuentes largas (Wikipedia, articulos extensos) cuando el agente es el LLM:
```bash
brain plan-direct-enrich "Nombre Entidad" --url "https://..." --config config/vault.yaml
```
Descarga la fuente completa, la guarda como raw, la divide en contextos multi-pass, rankea chunks por subtipo y genera un plan reusable para que Claude/Codex sigan la misma estructura sin usar API.

### Para fuentes largas cuando SI quieres el pipeline con proveedor:
```bash
brain multi-enrich "Nombre Entidad" --url "https://..." --llm-provider openai --config config/vault.yaml
```

### Persistencia de raw source:
Post-process con `--source-url` descarga y guarda automaticamente la fuente raw completa en `.brain-ops/raw/`. Esto permite re-procesamiento futuro y auditoria.

### Flujo estandar sin API para entidades grandes:
1. `brain create-entity "Nombre Entidad" --type person --config config/vault.yaml` si la entidad no existe
2. `brain plan-direct-enrich "Nombre Entidad" --url "https://..." --config config/vault.yaml`
3. Claude/Codex redacta la nota usando las pasadas generadas
4. `brain post-process "Nombre Entidad" --source-url "https://..." --config config/vault.yaml`
5. `brain check-coverage "Nombre Entidad" --config config/vault.yaml`
6. Si hace falta, otra pasada directa enfocada y `post-process` otra vez

### Lo que la escritura directa SOLA no hace antes de post-process:
- Persistir raw source automaticamente
- Guardar el extraction record automaticamente
- Sincronizar el entity registry automaticamente
- Compilar de regreso a SQLite automaticamente
- Disparar creacion automatica de entidades

---

## Senales — nunca mezclarlas

- `source_count` = evidencia de fuentes ingestadas (solo el pipeline API incrementa esto)
- `query_count` = interes del usuario por preguntas realizadas (solo query-knowledge incrementa esto)
- `relation_count` = conexiones del grafo
- `gap_count` = entidades faltantes en respuestas de queries

---

## Seguridad

- Nunca almacenar secretos en el vault ni hacer commit de ellos
- Nunca ejecutar comandos destructivos sin preguntar
- Preferir ediciones pequenas y reversibles
- Mantener los tests pasando antes de hacer commit
