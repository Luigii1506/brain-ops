# Important Current Flows

## Flow: user message to action

- Telegram/OpenClaw receives input
- handle_input_service processes it
- intent parser resolves intent
- intent execution triggers domain logic
- follow-up service handles missing info
- result is stored and/or reported

## Flow: life ops logging

- user logs expense/meal/workout
- service validates input
- SQLite stores structured data
- summaries/reports may be generated later
- Obsidian may receive durable notes/summaries

## Flow: knowledge capture

- notes/research captured
- Obsidian is the durable destination
- linked summaries/maps may be created
