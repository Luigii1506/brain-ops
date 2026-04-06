# brain-ops Usage Guide

## Setup

### 1. Configure your LLM provider

Add to your shell profile (`~/.zshrc`):

```bash
# Primary LLM (cheap, good quality)
export BRAIN_OPS_LLM_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="sk-your-key-here"

# Alternative providers (optional, switch with --llm-provider flag):
# export GEMINI_API_KEY="your-key"       # Google Gemini (free tier available)
# export OPENAI_API_KEY="your-key"       # OpenAI GPT-4o mini
```

### 2. Initialize brain-ops

```bash
brain init-db --config config/vault.yaml    # SQLite database
brain init-jobs                              # Scheduled cron jobs
```

### 3. Set up cron (Mac mini)

```bash
brain show-crontab                           # Print crontab entries
crontab -e                                   # Paste the output
```

---

## Use Cases

### Notas personales (tu notepad, reflexiones, diario)

Tienes notas sueltas, pensamientos, reflexiones de tu día. El sistema las procesa y extrae lo importante.

```bash
# Ingest texto directo (tus notas, pensamientos, reflexiones)
brain ingest-source "Hoy aprendí que la clave del clean code es nombrar bien las variables. En el proyecto de oharatcg me di cuenta que los nombres genéricos como 'data' y 'result' hacen el código ilegible." --use-llm --config config/vault.yaml

# Ingest notas largas desde un archivo
cat ~/Desktop/mis-notas-del-dia.txt | xargs -0 brain ingest-source --use-llm --config config/vault.yaml

# El LLM va a:
# - Extraer los temas clave (clean code, naming conventions)
# - Crear wikilinks a entidades [[Clean Code]], [[oharatcg]]
# - Guardar un TLDR y por qué importa para ti
```

### Libros

Cuando lees un libro y tomas notas por capítulo.

```bash
# 1. Crear la entidad del libro
brain create-entity "Sapiens" --type book --config config/vault.yaml

# 2. Enrichir con info del LLM
brain enrich-entity "Sapiens" --auto-generate --llm-provider deepseek --config config/vault.yaml

# 3. Ingest tus notas de cada capítulo
brain ingest-source "Capítulo 3 de Sapiens: La revolución cognitiva permitió a Homo sapiens cooperar en grupos grandes gracias al lenguaje y la capacidad de crear mitos compartidos. Esto les dio ventaja sobre Neandertales." --use-llm --title "Sapiens - Cap 3 Revolución Cognitiva" --config config/vault.yaml

# 4. El LLM extrae entidades y las vincula:
# → [[Sapiens]], [[Homo sapiens]], [[Revolución cognitiva]], [[Neandertales]]
```

### Artículos web

Encuentras un artículo interesante y quieres integrarlo a tu wiki.

```bash
# Ingest directo desde URL
brain ingest-source --url "https://es.wikipedia.org/wiki/Alejandro_Magno" --use-llm --config config/vault.yaml

# El sistema:
# 1. Descarga la página
# 2. Limpia HTML (quita nav, footer, scripts)
# 3. Clasifica el tipo (encyclopedia, article, etc.)
# 4. LLM extrae resumen, ideas clave, entidades
# 5. Crea nota en 01-Sources con TLDR y wikilinks
# 6. Auto-compila a SQLite

# Artículo de Medium/Substack
brain ingest-source --url "https://medium.com/@author/article-about-react-patterns" --use-llm --config config/vault.yaml

# Documentación técnica
brain ingest-source --url "https://docs.python.org/3/library/asyncio.html" --use-llm --config config/vault.yaml
```

### Videos (YouTube, podcasts)

Para videos necesitas el transcript. Opciones:

```bash
# Opción 1: Copia el transcript manualmente de YouTube
# (YouTube → ... → Show transcript → copiar texto)
brain ingest-source "Transcript del video de Fireship sobre React Server Components: RSC permite renderizar componentes en el servidor..." --use-llm --title "Fireship - React Server Components" --config config/vault.yaml

# Opción 2: Usa una herramienta de transcript
# ytdl-transcript (npm) o whisper (local)
# whisper video.mp4 --output-format txt
# brain ingest-source "$(cat video.txt)" --use-llm --title "Video sobre X" --config config/vault.yaml
```

### Páginas web que quieres monitorear

Para detectar cambios en páginas (precios, noticias, docs).

```bash
# Registrar fuente
brain add-source "react-docs" --url "https://react.dev/blog" --type web --selector ".blog-post-list" --config config/vault.yaml

# Registrar API
brain add-source "github-releases" --url "https://api.github.com/repos/facebook/react/releases" --type api --config config/vault.yaml

# Verificar cambios
brain check-source "react-docs"
# → Muestra: "Content changed (grew, delta: +342 chars)"
# → Muestra diff textual de qué cambió
# → Emite evento al event log

# Verificar todas las fuentes (cron diario)
brain check-all-sources
```

### Documentos de proyectos de programación

Para tus proyectos de dev (oharatcg, dolarin, sentinel, etc.).

```bash
# Ya tienes los proyectos registrados. Actualiza el contexto:
brain update-project-context "oharatcg" \
  --phase "Migración a Next.js 15" \
  --pending "Migrar pages router a app router" \
  --pending "Actualizar auth a BetterAuth" \
  --decision "Usar server components por default" \
  --notes "El deploy está en Vercel. La DB es PostgreSQL en Supabase."

# Genera CLAUDE.md para que Codex/Claude tengan contexto
brain generate-claude-md "oharatcg"
# → Escribe CLAUDE.md en ~/Documents/GitHub/oharatcg/CLAUDE.md

# Genera para todos los proyectos de una vez
brain generate-all-claude-md

# Ingest documentación como conocimiento
brain ingest-source "Oharatcg usa Next.js con app router. Para correr: npm run dev. Para deploy: vercel --prod. La base de datos está en Supabase con schema en prisma/schema.prisma." --use-llm --title "oharatcg - Setup Guide" --config config/vault.yaml
```

### Conocimiento general (historia, ciencia, geografía)

Para tu enciclopedia personal.

```bash
# Crear entidades
brain create-entity "Alejandro Magno" --type person --config config/vault.yaml
brain create-entity "Batalla de Gaugamela" --type event --config config/vault.yaml
brain create-entity "Macedonia" --type place --config config/vault.yaml
brain create-entity "Estoicismo" --type concept --config config/vault.yaml
brain create-entity "Segunda Guerra Mundial" --type war --config config/vault.yaml
brain create-entity "Renacimiento" --type era --config config/vault.yaml

# Auto-generar contenido con LLM
brain enrich-entity "Alejandro Magno" --auto-generate --llm-provider deepseek --config config/vault.yaml
# → LLM genera biografía completa, contribuciones, eventos, con wikilinks

# Agregar info nueva
brain enrich-entity "Alejandro Magno" --info "Según Plutarco, Alejandro dormía con una copia de la Ilíada bajo su almohada" --llm-provider deepseek --config config/vault.yaml

# Ingest desde Wikipedia
brain ingest-source --url "https://es.wikipedia.org/wiki/Estoicismo" --use-llm --config config/vault.yaml

# Ver tu enciclopedia
brain entity-index --config config/vault.yaml

# Ver relaciones
brain entity-relations "Alejandro Magno" --config config/vault.yaml

# Preguntar a tu wiki
brain query-knowledge "Qué relación hay entre Alejandro Magno y Aristóteles" --llm-provider deepseek --config config/vault.yaml

# Guardar la respuesta como nota permanente
brain query-knowledge "Qué impacto tuvo Alejandro en la difusión del helenismo" --file-back --llm-provider deepseek --config config/vault.yaml
```

### Banderas, capitales, datos tabulares

Para quizzes y aprendizaje.

```bash
# Crear entidades tipo place con datos
brain create-entity "Grecia" --type place --config config/vault.yaml
brain enrich-entity "Grecia" --info "Capital: Atenas. Continente: Europa. Población: 10.4 millones. Idioma: Griego. Moneda: Euro." --llm-provider deepseek --config config/vault.yaml

# Compilar a SQLite para apps
brain compile-knowledge --config config/vault.yaml

# La API ya sirve los datos
brain serve-api --port 8420
# GET http://localhost:8420/entities?entity_type=place → todas las countries
# GET http://localhost:8420/entities/Grecia → datos de Grecia
```

---

## Preguntar a tu segundo cerebro

```bash
# Preguntas simples
brain query-knowledge "Quién fue Aristóteles" --llm-provider deepseek --config config/vault.yaml

# Preguntas sobre ti
brain query-knowledge "En qué proyectos estoy trabajando y cuál es el estado de cada uno" --config config/vault.yaml

# Preguntas de relaciones
brain query-knowledge "Qué personajes históricos están relacionados con Grecia" --llm-provider deepseek --config config/vault.yaml

# Preguntas de programación
brain query-knowledge "Cómo corro el proyecto oharatcg y qué stack usa" --config config/vault.yaml

# Guardar respuestas valiosas
brain query-knowledge "Resume la filosofía estoica y cómo aplicarla hoy" --file-back --llm-provider deepseek --config config/vault.yaml
```

---

## Integración con NotebookLM de Google

NotebookLM no tiene API pública. Pero puedes usarlo así:

1. **Exporta tu wiki como fuentes para NotebookLM:**
   - Tu vault de Obsidian son archivos .md
   - Sube los archivos de `02 - Knowledge/` a NotebookLM como fuentes
   - NotebookLM puede generar podcasts, Q&A, y resúmenes sobre TU conocimiento

2. **El flujo inverso:**
   - Haz preguntas en NotebookLM sobre tus notas
   - Las respuestas interesantes → `brain ingest-source "respuesta..." --use-llm`
   - Se integran de vuelta a tu wiki

3. **Alternativa real (sin NotebookLM):**
   - `brain query-knowledge` ya hace lo mismo — sintetiza respuestas de tus notas
   - La diferencia: NotebookLM tiene interfaz bonita, brain-ops tiene CLI + API

---

## Búsqueda

```bash
# Buscar en todo el vault
brain search-knowledge "Macedonia" --config config/vault.yaml

# Buscar solo entidades
brain search-knowledge "guerra" --entity-only --config config/vault.yaml

# Buscar con JSON output
brain search-knowledge "programación" --json --config config/vault.yaml
```

---

## Mantenimiento automático (cron)

```bash
# Ver qué jobs están configurados
brain list-jobs

# Ver crontab para copiar
brain show-crontab
# Output:
# 0 6 * * * brain-ops check-all-sources    # check-all-sources (daily 6am)
# 0 6 * * * brain-ops compile-knowledge    # compile-knowledge (daily 6am)
# 0 6 * * * brain-ops entity-index         # entity-index (daily 6am)
# 0 6 * * 1 brain-ops audit-vault          # audit-vault (weekly Monday 6am)

# Auditar vault manualmente
brain audit-vault --config config/vault.yaml
```

---

## API para frontends

```bash
# Levantar API
brain serve-api --port 8420

# Endpoints disponibles:
# Knowledge
# GET /entities/                     → lista todas las entidades
# GET /entities/types                → tipos de entidad disponibles
# GET /entities?entity_type=person   → filtrar por tipo
# GET /entities/Alejandro Magno      → una entidad
# GET /entities/Alejandro Magno/relations → conexiones

# Projects
# GET /projects/                     → todos los proyectos
# GET /projects/brain-ops            → un proyecto
# GET /projects/brain-ops/context    → contexto del proyecto
# PUT /projects/brain-ops/context    → actualizar contexto

# Sources
# GET /sources/                      → fuentes monitoreadas
# POST /sources/new-source           → agregar fuente
# DELETE /sources/old-source         → eliminar fuente

# Personal (life-ops)
# GET /personal/meals?date=2026-04-05
# GET /personal/expenses?date=2026-04-05
# GET /personal/workouts
# GET /personal/habits
# GET /personal/body-metrics
# GET /personal/supplements
```

### Frontend con React/Next.js

```bash
# Crear frontend
npx create-next-app brain-ops-dashboard
cd brain-ops-dashboard

# Consumir la API
# fetch('http://localhost:8420/entities?entity_type=person')
# fetch('http://localhost:8420/personal/meals?date=2026-04-05')
# fetch('http://localhost:8420/projects/')
```

---

## Switching LLM providers

```bash
# Usar DeepSeek (por defecto si configurado)
brain ingest-source --url "..." --use-llm --config config/vault.yaml

# Usar Gemini para una operación específica
brain query-knowledge "..." --llm-provider gemini --config config/vault.yaml

# Usar Ollama local (sin costo)
brain enrich-entity "..." --auto-generate --llm-provider ollama --config config/vault.yaml

# Cambiar provider por defecto
export BRAIN_OPS_LLM_PROVIDER="gemini"
```

---

## Environment variables

| Variable | Propósito | Default |
|----------|-----------|---------|
| `BRAIN_OPS_LLM_PROVIDER` | LLM provider default | `ollama` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `BRAIN_OPS_EVENT_LOG` | Event log path | - |
| `BRAIN_OPS_PROJECT_REGISTRY` | Project registry | `~/.brain-ops/projects.json` |
| `BRAIN_OPS_SOURCE_REGISTRY` | Source registry | `~/.brain-ops/sources.json` |
| `BRAIN_OPS_JOB_REGISTRY` | Job registry | `~/.brain-ops/jobs.json` |
| `BRAIN_OPS_KNOWLEDGE_DB` | Knowledge SQLite | `{vault}/.brain-ops/knowledge.db` |
| `BRAIN_OPS_DATABASE` | Life-ops SQLite | `data/brain_ops.db` |
