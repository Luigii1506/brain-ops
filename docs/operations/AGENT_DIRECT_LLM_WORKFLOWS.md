# Agent Direct-LLM Workflows

This guide defines the standard way to use Claude Code or Codex as the LLM directly, while preserving as much of the real `brain-*` pipeline as possible.

The goal is:
- avoid API cost when the agent can do the thinking,
- keep the same operational closing steps as the real pipeline,
- preserve raw source, traceability, registry sync, and compilation whenever possible,
- give both Claude and Codex the same reusable workflow.

---

## Core Rule

When the user is already talking to Claude/Codex, the agent itself is the LLM.

That means:
- do **not** spend provider budget by default on `--llm-provider` or `--use-llm`,
- do use official deterministic commands before and after the agent writes,
- do close the loop with `post-process`, `compile`, `check-coverage`, or equivalent workflow steps.

---

## Command Mapping

| Official provider workflow | Direct-agent standard | Status |
| --- | --- | --- |
| `brain enrich-entity --url/--info --llm-provider ...` | Agent writes directly into the entity note, then `brain post-process` | Supported |
| `brain multi-enrich --url ... --llm-provider ...` | `brain plan-direct-enrich` + agent writes pass by pass + `brain post-process` + `brain check-coverage` | Supported |
| `brain ingest-source --use-llm` | `brain ingest-source` without LLM to create the source note deterministically, then agent upgrades the note manually if needed | Partial |
| `brain query-knowledge --llm-provider ...` | `brain query-knowledge` without LLM or `brain search-knowledge`, then agent synthesizes from the grounded notes | Supported |
| `brain query-knowledge --file-back --llm-provider ...` | Agent synthesizes grounded answer, then saves the answer note manually | Partial |
| `brain route-input --use-llm` | Agent interprets the request directly in chat; use `route-input --no-use-llm` only for debugging heuristics | Supported |
| `brain handle-input --use-llm` | Agent interprets and executes canonical commands directly; use `handle-input` when you want the product pipeline, not because the agent needs help parsing | Supported |

---

## Standard Workflows

### 1. Large entity from URL

Use this for:
- people,
- empires,
- civilizations,
- wars,
- battles,
- books,
- countries,
- disciplines,
- long Wikipedia pages,
- any source that should be covered in batches.

#### Standard commands

```bash
brain create-entity "Entity Name" --type person --config config/vault.yaml
brain plan-direct-enrich "Entity Name" --url "https://..." --config config/vault.yaml
```

The agent then:
1. opens the generated plan in `.brain-ops/direct-enrich/<slug>.json`,
2. writes the note pass by pass,
3. preserves frontmatter and `related`,
4. closes with:

```bash
brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml
brain check-coverage "Entity Name" --config config/vault.yaml
```

If coverage still shows important gaps:
1. do one more focused direct pass,
2. run `brain post-process` again.

#### Prompt template

```text
Use the direct-agent large-entity workflow from the repo.

Entity: <Entity Name>
URL: <https://...>
Type: <person|war|book|...>

Steps:
1. Create the entity if it does not exist.
2. Run brain plan-direct-enrich with the URL.
3. Read the generated pass plan and raw source.
4. Write the entity note pass by pass, covering all high-priority sections and the valuable medium-priority ones.
5. Keep frontmatter related links updated.
6. Run brain post-process with the same source URL.
7. Run brain check-coverage.
8. If high-priority gaps remain, do one more focused pass and post-process again.
```

---

### 2. Small entity or lightweight enrichment

Use this for:
- simple concepts,
- small places,
- animals,
- short biographies,
- smaller pages where batch planning is unnecessary.

#### Standard commands

```bash
brain create-entity "Entity Name" --type concept --config config/vault.yaml
```

The agent then writes directly and closes with:

```bash
brain post-process "Entity Name" --source-url "https://..." --config config/vault.yaml
brain check-coverage "Entity Name" --config config/vault.yaml
```

#### Prompt template

```text
Use the direct-agent lightweight entity workflow.

Entity: <Entity Name>
URL or source: <optional>
Type: <concept|place|animal|...>

Steps:
1. Create the entity if it does not exist.
2. Write a compact but complete note directly.
3. Keep frontmatter related links updated.
4. Run brain post-process with the source URL if one was used.
5. Run brain check-coverage if the source is non-trivial.
```

---

### 3. Source ingest without provider

Use this when the official command would normally be:

```bash
brain ingest-source --url "https://..." --use-llm --config config/vault.yaml
```

#### Standard commands

```bash
brain ingest-source --url "https://..." --config config/vault.yaml
```

This deterministic path already gives you:
- source note creation,
- raw source persistence,
- source metadata,
- note creation under sources.

Then the agent may:
1. open the created source note,
2. refine summary, key insights, entities, or relevance manually using the raw source,
3. run:

```bash
brain compile-knowledge --config config/vault.yaml
```

#### Important limitation

There is currently no dedicated `post-process` equivalent for source notes that fully mirrors provider-based ingest extraction.

So this workflow is:
- operationally useful,
- low-cost,
- but not yet full parity with `ingest-source --use-llm`.

#### Prompt template

```text
Use the direct-agent source-ingest workflow.

Source URL or text: <source>
Optional title: <title>

Steps:
1. Run brain ingest-source without --use-llm to create the deterministic source note.
2. Open the created source note and the saved raw source.
3. Improve the source note manually so it contains a strong summary, key insights, mentioned entities, and personal relevance when justified.
4. Run brain compile-knowledge.
5. If the source should promote durable knowledge, continue with promote-note or direct entity enrichment.
```

---

### 4. Grounded knowledge query without provider

Use this when the official command would normally be:

```bash
brain query-knowledge "..." --llm-provider openai --config config/vault.yaml
```

#### Standard commands

Option A:

```bash
brain query-knowledge "..." --config config/vault.yaml
```

Option B:

```bash
brain search-knowledge "..." --config config/vault.yaml --json
```

The agent then:
1. reads the relevant notes,
2. synthesizes an answer grounded only in those notes,
3. explicitly says when the notes are insufficient.

If you want the result filed back:
- the agent should create the answer note manually,
- because `--file-back` currently depends on the provider-backed synthesis path.

#### Prompt template

```text
Answer this using the direct-agent grounded query workflow.

Question: <question>

Steps:
1. Run brain query-knowledge without provider, or search-knowledge if you need broader recall.
2. Open the notes that were retrieved.
3. Synthesize an answer grounded only in those notes.
4. If the notes are insufficient, say so clearly instead of guessing.
5. If I ask for file-back, save the answer note manually after writing it.
```

---

### 5. Natural-language routing and execution when already in chat

Use this for:
- `route-input --use-llm`
- `handle-input --use-llm`

#### Standard rule

If the user is already speaking to Claude/Codex, the agent is already the interpreter.

So the standard direct-agent behavior is:
1. understand the request directly,
2. choose the canonical command(s),
3. execute them,
4. return the result.

Use `route-input` or `handle-input` only when:
- you want to test the product pipeline itself,
- or you want to debug the CLI behavior,
- not because the agent needs help understanding the user.

#### Prompt template

```text
Treat this as a direct-agent execution request, not as a provider-routed chat.

Steps:
1. Interpret my intent directly.
2. Choose the canonical brain command(s) or workflow(s).
3. Execute them.
4. If needed, use route-input or handle-input only to validate the product pipeline, not as the main reasoning path.
```

---

## Prompt Shortcuts

These are the short prompts you can reuse in either Claude or Codex.

### Large entity

```text
Use the repo's direct-agent large-entity workflow for <Entity Name> with <URL>. Plan with plan-direct-enrich, write by passes, then post-process and check-coverage.
```

### Small entity

```text
Use the repo's direct-agent lightweight entity workflow for <Entity Name>. Create it if needed, write directly, then post-process.
```

### Source ingest

```text
Use the repo's direct-agent source-ingest workflow for <URL or text>. Run deterministic ingest-source first, then improve the source note manually and compile.
```

### Grounded query

```text
Use the repo's direct-agent grounded query workflow for this question. Retrieve notes first, then answer only from those notes.
```

### Natural language command execution

```text
Treat this as a direct-agent command request. Interpret it yourself and execute canonical brain workflows directly.
```

---

## Recommended Policy

For both Claude and Codex:
- use provider-backed commands when you explicitly want the product's built-in LLM path,
- use direct-agent workflows when the agent is already in the loop and you want to save cost,
- always preserve the closing steps of the real pipeline,
- prefer deterministic preparation + manual synthesis over ad hoc editing.

That gives the best balance between:
- cost,
- traceability,
- quality,
- and consistent behavior across agents.
