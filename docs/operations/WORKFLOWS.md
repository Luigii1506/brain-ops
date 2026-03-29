# Operational Workflows

## 1. Capture workflow

Input channels:
- manual note capture
- terminal
- agent-created note
- imported article
- repo-derived docs
- daily notes
- quick idea capture

Destination:
- `00 - Inbox/`

Processing rules:
- raw notes should not remain in inbox indefinitely
- inbox notes should later become source notes, permanent notes, project notes, or archived notes

## 2. Inbox processing workflow

Expected command:
- `brain process-inbox`

Steps:
1. scan inbox notes
2. detect note intent
3. add or normalize frontmatter
4. enrich content if needed
5. move to correct folder
6. optionally create related links
7. produce processing report

## 3. Project documentation workflow

Expected command:
- `brain create-project "<Project Name>"`

Should create:
- project home note
- architecture note
- decisions note
- debugging note
- changelog note
- runbook note

## 4. Script documentation workflow

Expected command:
- `brain document-script /path/to/script.py`

Should produce:
- what it does
- inputs
- outputs
- dependencies
- how to run it
- failure modes
- related project

## 5. Source ingestion workflow

Expected command:
- `brain ingest-source "<title>"`

Possible source types:
- article
- paper
- documentation
- book chapter
- video notes

Should output:
- summary
- key ideas
- reusable insights
- links to related MOCs or knowledge notes

## 6. Weekly review workflow

Expected command:
- `brain weekly-review`

Should produce:
- unprocessed inbox items
- stale project notes
- orphan notes
- notes missing frontmatter
- recently changed important notes
- suggested follow-ups

## 7. Repository documentation workflow

Potential future command:
- `brain document-repo /path/to/repo`

Should generate:
- project summary
- stack overview
- local setup guide
- key scripts
- architecture outline
- debugging notes
- important commands
- glossary
