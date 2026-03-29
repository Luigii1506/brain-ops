# Recommended Vault Structure

```text
00 - Inbox/
01 - Sources/
02 - Knowledge/
03 - Maps/
04 - Projects/
05 - Systems/
06 - Daily/
07 - Archive/
Templates/
Assets/
```

## Folder intent

### 00 - Inbox
Raw capture and temporary intake.

### 01 - Sources
Material tied to an external source:
- articles
- videos
- books
- docs
- papers
- websites

### 02 - Knowledge
Durable understanding and reusable notes:
- concepts
- facts
- world knowledge
- technical ideas
- personal lessons
- reflections worth keeping

This folder may include:
- `status: stub`
- `status: draft`
- mature notes

### 03 - Maps
Navigation only.

Maps of content, hubs, indexes, and entry-point notes belong here.
MOCs should not live inside content folders.

### 04 - Projects
Active work with bounded outcomes:
- repos
- initiatives
- implementation plans
- pending work
- architecture and debugging context tied to a project

### 05 - Systems
Operational knowledge:
- commands
- SOPs
- runbooks
- security procedures
- workflows
- reports

### 06 - Daily
Human-readable day summaries, reflections, and rollups.

This should not become the only place where structured life data lives.

### 07 - Archive
Legacy, deprecated, preserved, or inactive material.

## Note ontology

Primary `type` values:
- `source`
- `knowledge`
- `map`
- `project`
- `system`
- `command`
- `security_note`
- `daily`
- `inbox`

Secondary metadata examples:
- `status: stub`
- `status: draft`
- `status: active`
- `source_type: youtube`
- `knowledge_kind: country`

## What should stay out of the vault

- production secrets
- raw high-frequency numeric logs
- every meal/workout/expense as freeform markdown
- temporary machine-only artifacts

## Relationship to SQLite

The vault is the memory layer.
SQLite is the operational data layer.

Use the vault for:
- meaning
- synthesis
- context
- reflection

Use SQLite for:
- exact entries
- repeated logs
- calculations
- summaries that need precision
