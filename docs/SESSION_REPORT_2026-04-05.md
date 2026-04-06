# Session Report — 2026-04-05

## Stats

- **Commits today:** 20 (10 pre-LLM-wiki + 10 LLM-wiki)
- **Lines added:** ~8,000+
- **Lines removed:** ~300
- **Files created:** 25+
- **Tests:** 393 passing
- **New CLI commands:** 25+

---

## WHAT WAS BUILT — Complete list

### Phase 1: Migration cleanup + Action Plan (commits 63f1264 → 657f3ee)

| What | Status |
|------|--------|
| Delivery presets (alert automation) | ✅ Done |
| Remove 6 deprecated service wrappers | ✅ Done |
| Action Plan document | ✅ Done |

### Phase 2: Action Plan Blocks A-F (commits d9cdc13 → d0147c0)

| Block | What | Status |
|-------|------|--------|
| A | Knowledge entity model (10 types, frontmatter schemas, entity creation) | ✅ Done |
| A | Entity index generation | ✅ Done |
| A | Entity relationship extraction | ✅ Done |
| B | Projects domain (registry, context, CLAUDE.md generation) | ✅ Done |
| C | Monitoring/scraping (sources, snapshots, diffs) | ✅ Done |
| D | Knowledge compile (Obsidian → SQLite) | ✅ Done |
| E | Scheduling primitives (cron jobs, crontab generation) | ✅ Done |
| F | REST API (FastAPI, 4 route modules) | ✅ Done |

### Phase 3: LLM Wiki System (commits 14eff37 → f3596a5)

| What | Status |
|------|--------|
| Entity routing fix (entities → 02-Knowledge instead of Inbox) | ✅ Done |
| BeautifulSoup selector parsing for scraping | ✅ Done |
| Textual diff output for check-source | ✅ Done |
| Event log integration for source checks | ✅ Done |
| Knowledge search (search-knowledge command) | ✅ Done |
| Batch generate-all-claude-md | ✅ Done |
| API write endpoints (PUT context, POST/DELETE sources) | ✅ Done |
| Ingest pipeline with URL support | ✅ Done |
| Compile-on-change (auto compile after entity creation) | ✅ Done |
| Multi-provider LLM client (Ollama, DeepSeek, Gemini, OpenAI, Claude) | ✅ Done |
| URL ingest (download → classify → extract → notes + wikilinks) | ✅ Done |
| Entity enrichment from URL/text/auto-generate | ✅ Done |
| Query synthesis (search wiki → LLM answer → file back) | ✅ Done |
| Smart LLM router (fast tier for extract, quality tier for writing) | ✅ Done |
| Structured intelligence extraction (facts, timeline, relationships, insights, contradictions) | ✅ Done |
| Standardized sections per entity type | ✅ Done |
| Entity registry with learning (aliases, confidence, source count) | ✅ Done |
| User preference profile | ✅ Done |
| Known entity injection into prompts | ✅ Done |
| Universal knowledge object model (object_kind + subtype) | ✅ Done |
| 40+ subtype-specific section templates | ✅ Done |
| Canonical predicate vocabulary (30+ predicates, 50+ normalizations) | ✅ Done |
| Disambiguation support | ✅ Done |
| Entity promotion rules (mention → candidate → canonical) | ✅ Done |
| Full extraction JSON persistence | ✅ Done |

---

## WHAT IS GOOD

### Architecture
- **Clean layer separation**: domains (pure logic) → application (workflows) → interfaces (CLI/API)
- **Dependency injection**: all workflows accept injected functions for testability
- **No vendor lock-in on LLM**: 5 providers supported, switchable by env var
- **Event-driven**: every operation emits events to the event log
- **Compile pattern**: Obsidian as source of truth, SQLite as derived/queryable output

### Knowledge System
- **Structured extraction**: not just summaries — facts, timeline, relationships, insights, contradictions
- **Learning loop**: entity registry accumulates intelligence across ingest operations
- **Canonical predicates**: relationships are normalized (ES/EN), not free-form chaos
- **Section templates per subtype**: planets get Orbit/Atmosphere, books get Themes/Quotes
- **Extraction persistence**: full LLM JSON saved for replay and debugging
- **User preferences**: injected into prompts so the system learns your style

### Real Test
- **Alejandro Magno from Wikipedia actually works**: OpenAI GPT-4o mini enriched the entity with real biographical data, wikilinks, and structured sections in one API call for $0.0005

---

## WHAT IS BAD / INCOMPLETE

### Not wired yet (code exists but not connected)
1. **object_model.py is not used by create-entity or enrich-entity yet** — the subtype-specific sections exist but `entities.py` still uses `_STANDARD_SECTIONS` for all types. The new `sections_for_subtype()` function exists but nothing calls it.
2. **normalize_predicate() is not called anywhere** — the canonical predicate vocabulary exists but relationships from ingest are still stored with raw LLM predicates.
3. **Promotion rules exist but no workflow uses them** — `should_promote_to_candidate()` and `should_promote_to_canonical()` are defined but never called.
4. **Disambiguation exists but no workflow uses it** — `build_disambiguated_name()` and `needs_disambiguation()` are defined but never called.
5. **Extraction store saves JSON but nothing reads it back** — records are saved but there's no command to list/replay/re-process extractions.

### Missing tests
6. **No tests for object_model.py** — predicate normalization, promotion rules, sections_for_subtype, disambiguation
7. **No tests for extraction_store.py** — save/load roundtrips
8. **No tests for registry.py** — learn_from_ingest, alias resolution, confidence updates
9. **No tests for preferences.py** — load/save roundtrips
10. **No tests for search.py** — search_notes function
11. **No tests for LLM client** — can't test API calls but can test resolve_provider, normalize_predicate
12. **Ingest tests only cover the old IngestPlan shape** — new fields (core_facts, timeline, relationships, etc.) not tested

### Architectural gaps
13. **No raw source persistence** — the downloaded HTML/text is discarded after processing. Should save to `{vault}/.brain-ops/raw/`
14. **Compile doesn't populate entity_facts, entity_timeline, entity_insights tables** — the tables exist in SQLite but `write_compiled_entities` only writes entities and relations
15. **search-knowledge is substring match only** — no BM25, no embeddings, no ranked results
16. **entity-relations only shows direct connections** — no graph traversal (2+ hops)
17. **API has no search endpoint** — no `GET /entities/search?q=...`
18. **No lint/health-check command that uses the registry** — audit-vault exists but doesn't check for duplicate entities, orphan aliases, or stale confidence

### Data model gaps
19. **object_kind is not stored in frontmatter** — entities still use `type: person` not `object_kind: entity, subtype: person`
20. **No concept vs topic distinction in practice** — the model defines it but create-entity still uses the flat type list
21. **entity_registry.json and SQLite knowledge.db are not synced** — two separate stores of entity intelligence
22. **No source_id tracking** — facts and timeline items have `source_id` column but it's never populated

---

## WHAT TO DO NEXT — Priority order

### P0: Wire what's already built (no new code, just connect)
1. **Make create-entity use sections_for_subtype()** instead of `_STANDARD_SECTIONS`
2. **Make ingest normalize predicates** with `normalize_predicate()` before saving to registry
3. **Make compile populate entity_facts/timeline/insights** from frontmatter or extraction records

### P1: Add missing tests
4. Tests for object_model.py (predicate normalization, promotion, sections)
5. Tests for registry.py (learn_from_ingest, aliases, confidence)
6. Tests for extraction_store.py (save/load)

### P2: Close data model gaps
7. **Update frontmatter to include object_kind/subtype** — or at minimum keep a mapping
8. **Populate source_id** when writing facts/timeline from ingest
9. **Add API search endpoint** — `GET /entities/search?q=...`

### P3: Improve quality
10. **Add raw source persistence** — save downloaded content to `.brain-ops/raw/`
11. **Add extraction replay command** — `brain replay-extraction {file}` to re-process saved JSON
12. **Add registry lint command** — detect duplicates, orphan aliases, low-confidence entities

### P4: Future features
13. BM25 or hybrid search
14. Graph traversal (2+ hops)
15. Entity auto-creation from high-importance mentions
16. Frontend dashboard

---

## FILE MAP — New files created this session

```
src/brain_ops/
  ai/
    llm_client.py                    ← Multi-provider LLM (Ollama/DeepSeek/Gemini/OpenAI/Claude)
  domains/
    knowledge/
      compile.py                     ← Obsidian frontmatter → SQLite compiler
      enrichment_llm.py              ← LLM prompts for entity enrichment/generation
      entities.py                    ← Entity types, schemas, frontmatter builders (UPDATED)
      extraction_store.py            ← Full LLM JSON persistence
      index.py                       ← Entity index generation
      ingest.py                      ← URL/text ingest with structured extraction
      object_model.py                ← Universal knowledge object model
      preferences.py                 ← User preference profile
      registry.py                    ← Entity registry with learning
      relations.py                   ← Relationship extraction and graph
      search.py                      ← Knowledge search
    monitoring/
      sources.py                     ← Source definitions and registry
      snapshots.py                   ← Snapshot capture (UPDATED with selector)
      diffs.py                       ← Change detection (UPDATED with text diff)
    projects/
      registry.py                    ← Project registry and context
      claude_md.py                   ← CLAUDE.md generator
  application/
    knowledge.py                     ← Knowledge workflows (UPDATED heavily)
    projects.py                      ← Project workflows (UPDATED)
    sources.py                       ← Source check workflows (UPDATED)
  interfaces/
    api/
      app.py                         ← FastAPI factory
      dependencies.py                ← API path resolution
      routes_entities.py             ← Knowledge entity endpoints
      routes_personal.py             ← Life-ops endpoints
      routes_projects.py             ← Project endpoints (UPDATED with PUT)
      routes_sources.py              ← Source endpoints (UPDATED with POST/DELETE)
    cli/
      knowledge.py                   ← Knowledge CLI presenters (UPDATED heavily)
      commands_notes.py              ← CLI commands (UPDATED)
      notes.py                       ← Note CLI (UPDATED)
      projects.py                    ← Project CLI (UPDATED)
      sources.py                     ← Source CLI (UPDATED)
      scheduling.py                  ← Scheduling CLI
      commands_scheduling.py         ← Scheduling commands
      commands_projects.py           ← Project commands (UPDATED)
      commands_sources.py            ← Source commands
  core/
    scheduling/
      jobs.py                        ← Scheduled job definitions
  storage/
    sqlite/
      entities.py                    ← Entity SQLite storage (UPDATED with new tables)

docs/
  USAGE_GUIDE.md                     ← Complete usage guide
  ai-context/ACTION_PLAN.md          ← Action plan document

tests/
  test_knowledge_entity_domain.py    ← Entity domain tests (UPDATED)
  test_knowledge_compile.py          ← Compile tests
  test_monitoring_sources.py         ← Monitoring tests
  test_projects_domain.py            ← Project tests
  test_scheduling.py                 ← Scheduling tests
  test_api_routes.py                 ← API route tests
```

---

## INTELLIGENCE ACCUMULATED FILES

```
{vault}/.brain-ops/
  entity_registry.json               ← Canonical names, aliases, confidence, frequent relations
  preferences.json                   ← Language, detail level, interests, style rules
  knowledge.db                       ← SQLite: entities, relations, facts, timeline, insights
  extractions/                       ← Full LLM JSON for every ingest (replay/debug)
    20260405-*.json

~/.brain-ops/
  projects.json                      ← 6 registered projects with context
  sources.json                       ← Monitored URLs
  jobs.json                          ← 4 scheduled cron jobs
  snapshots/                         ← Latest snapshot per source
```
