# Operational Workflows

## 1. Knowledge capture workflow

Input channels:
- OpenClaw chat
- terminal
- voice transcript
- pasted text
- URLs
- imported source material

Expected behavior:
1. detect intent
2. choose note type or structured data target
3. create or update the right artifact
4. improve structure if needed
5. link or promote later if useful

## 2. Inbox processing workflow

Expected command:
- `brain process-inbox`

Purpose:
- clear `00 - Inbox`
- classify notes
- apply frontmatter
- improve loose bodies
- move notes into canonical folders

## 3. Note enrichment workflow

Expected command:
- `brain enrich-note /path/to/note.md`

Pipeline:
1. improve structure
2. enrich with grounded research
3. apply likely internal links

## 4. Source-to-knowledge workflow

Expected command:
- `brain promote-note /path/to/source.md`

Purpose:
- extract durable knowledge from source material
- create a draft knowledge note
- keep attribution back to the source

## 5. Project documentation workflow

Expected command:
- `brain create-project "<Project Name>"`

Should create:
- project home note
- architecture note
- decisions note
- debugging note
- changelog note
- runbook note

## 6. Systems documentation workflow

Current commands involved:
- `brain capture`
- `brain improve-note`
- `brain enrich-note`

Target artifacts:
- command notes
- SOPs
- security notes
- runbooks
- setup guides

## 7. Nutrition logging workflow

Expected future command:
- `brain log-meal "..."`

Should:
1. parse the meal
2. store structured rows in SQLite
3. calculate daily totals
4. optionally write daily summary notes into the vault

## 8. Fitness logging workflow

Expected future command:
- `brain log-workout "..."`

Should:
1. parse exercises and sets
2. write structured workout rows
3. compare against recent sessions
4. optionally generate summaries or coaching notes

## 9. Expense logging workflow

Expected future command:
- `brain log-expense "..."`

Should:
1. capture amount, category, merchant, and note
2. store the transaction in SQLite
3. update budget summaries
4. produce weekly and monthly views when requested

## 10. Review workflow

Current commands:
- `brain audit-vault`
- `brain weekly-review`

Future extension:
- review vault health
- review meal adherence
- review workout progress
- review spending trends
- publish weekly summaries to Obsidian
