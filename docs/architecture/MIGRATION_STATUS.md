# Migration Status

## 1. Current Migration Summary

This repository is evolving from a conversation-centered personal assistant into a reusable operational core.

The direction remains:

- `brain-ops` as the real operational core
- OpenClaw and Telegram as interface/orchestration surfaces
- SQLite as the current structured operational store
- Obsidian as the durable knowledge/documentation layer
- Ollama as an auxiliary intelligence layer, not a hard dependency for critical operations

The migration strategy being followed is incremental and compatibility-first:

- create explicit destination modules first
- extract small reusable slices
- keep existing service files working as wrappers/adapters
- avoid moving storage-heavy logic too early
- avoid rewriting parser, CLI, OpenClaw, or follow-up flows until reusable capabilities are stronger

This is aligned with:

- `docs/ai-context/MASTER_MIGRATION_BLUEPRINT.md`
- `docs/ai-context/TARGET_ARCHITECTURE.md`

### OpenClaw interface boundary

Extracted into:

- [manifest.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/openclaw/manifest.py)

What moved:

- `OPENCLAW_MANIFEST`
- `serialize_openclaw_manifest(...)`
- `write_openclaw_manifest(...)`
- `build_openclaw_manifest_table(...)`

Current state:

- the static OpenClaw manifest now has an explicit home under `interfaces/openclaw/`
- manifest serialization, write-back, and table rendering now also have an explicit home under `interfaces/openclaw/`
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) now consumes the manifest from that interface boundary instead of owning it inline

### Application orchestration

Extracted into:

- [notes.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/application/notes.py)

Current state:

- note-oriented workflow execution now has a first explicit `application/` home above services and below CLI presentation
- `capture`, `create-note`, `create-project`, `daily-summary`, `improve`, `research`, `link`, `apply-links`, `promote`, and `enrich` execution paths now route through `application/notes.py`
- [interfaces/cli/notes.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/notes.py) now primarily owns vault loading plus presentation
- conversation-oriented workflow execution now also has a first explicit `application/` home in [conversation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/application/conversation.py)
- `route-input` and `handle-input` CLI execution paths now route through `application/conversation.py`
- [interfaces/cli/conversation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/conversation.py) now primarily owns config loading plus presentation
- personal workflow execution now also has a first explicit `application/` home in [personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/application/personal.py)
- personal status, logging, and target/diet-management CLI execution paths now route through `application/personal.py`
- [interfaces/cli/personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal.py), [personal_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal_logging.py), and [personal_management.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal_management.py) now primarily own runtime loading plus presentation
- knowledge-maintenance workflow execution now also has a first explicit `application/` home in [knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/application/knowledge.py)
- `process-inbox`, `weekly-review`, `audit-vault`, and `normalize-frontmatter` CLI execution paths now route through `application/knowledge.py`
- [interfaces/cli/knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/knowledge.py) now primarily owns runtime loading plus presentation
- system/bootstrap workflow execution now also has a first explicit `application/` home in [system.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/application/system.py)
- `info`, `init`, `init-db`, and `openclaw-manifest` CLI execution paths now route through `application/system.py`
- [interfaces/cli/system.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/system.py) and [openclaw.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/openclaw.py) now primarily own presentation over application workflows
- consolidation tests now also cover the new `application/` layer directly in [test_application_workflows.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_application_workflows.py)
- that application-level coverage now exercises representative orchestration for conversation routing/handling, knowledge maintenance, note creation, and personal datetime normalization
- that coverage now also exercises representative passthrough/mapping behavior for capture, research, enrich, spending-summary, budget-target, and diet-plan workflows at the `application/` boundary
- that coverage now also exercises system/bootstrap orchestration for config loading, config initialization, database initialization, and optional OpenClaw manifest write-back

### Personal domain consolidation

Additional extraction into domain modules:

- [goals.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/goals.py)
- [parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/diet/parsing.py)
- [projections.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/diet/projections.py)

What moved:

- `build_date_bounds(...)`
- `build_period_bounds(...)`
- `build_actual_meal_progress(...)`
- `resolve_macro_status_targets(...)`
- `normalize_macro_target_inputs(...)`
- `normalize_budget_target_inputs(...)`
- `normalize_habit_target_inputs(...)`
- `normalize_diet_plan_name(...)`
- `parse_diet_plan_meals(...)`
- `normalize_diet_meal_update_inputs(...)`
- `parse_diet_update_items(...)`
- `normalize_meal_log_input(...)`
- `normalize_supplement_log_inputs(...)`
- `normalize_habit_checkin_inputs(...)`
- `normalize_daily_log_inputs(...)`
- `normalize_workout_log_input(...)`
- `normalize_body_metrics_inputs(...)`
- `normalize_expense_log_inputs(...)`

Current state:

- [goals_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/goals_service.py) no longer owns inline date/period window construction for daily, weekly, and monthly status queries
- [goals_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/goals_service.py) no longer owns inline selection of macro targets from active diet vs manual target row
- [goals_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/goals_service.py) now also delegates write-input normalization for macro targets, budget targets, and habit targets to the personal domain
- [diet_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/diet_service.py) now also delegates plan-name normalization, meal-spec parsing, meal-update normalization, and parsed meal-item shaping to the diet domain
- [nutrition_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/nutrition_service.py) now also delegates meal-log input normalization and parsed-item validation to the nutrition domain
- [life_ops_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/life_ops_service.py) now also delegates supplement and habit-checkin write-input normalization to the personal tracking domain
- [daily_log_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_log_service.py) now also delegates daily-log text/domain normalization to the personal tracking domain
- [fitness_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/fitness_service.py) now also delegates workout-log input normalization and parsed-entry validation to the fitness domain
- [body_metrics_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/body_metrics_service.py) now also delegates body-metrics write-input validation to the personal tracking domain
- [expenses_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/expenses_service.py) now also delegates expense-log write-input normalization to the personal tracking domain
- [diet_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/diet_service.py) no longer owns inline aggregation of actual meal progress rows into per-meal buckets and totals
- direct domain coverage in [test_personal_domain_results.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_personal_domain_results.py) now also verifies date/period bounds, macro-target resolution, goal/diet/logging/body-metrics/workout/expense write-input normalization, and actual-meal-progress aggregation
- direct service coverage in [test_personal_logging_services.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_personal_logging_services.py) now also verifies that personal logging workflows preserve normalized domain inputs end-to-end in `dry_run` mode

### SQLite storage consolidation

Additional extraction into storage modules:

- [daily_summary.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/daily_summary.py)

What moved:

- `fetch_daily_summary_context_rows(...)`

Current state:

- [daily_summary_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_summary_service.py) now delegates the per-day SQLite fetch bundle for meals, supplements, workouts, expenses, habits, body metrics, and daily logs to [daily_summary.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/daily_summary.py)
- the daily summary service now keeps a single local context loader instead of seven nearly identical range-based loaders
- [inbox_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/inbox_service.py) and [normalize_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/normalize_service.py) now share `write_note_document_if_changed(...)` from [note_writing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_writing.py) for render/compare/write behavior
- direct workflow coverage in [test_inbox_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_inbox_service.py) now also verifies that inbox processing normalizes and moves source notes, while leaving ambiguous project-like notes in inbox
- direct workflow coverage in [test_review_and_audit_services.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_review_and_audit_services.py) now also verifies representative weekly-review and vault-audit behavior against a real temporary vault

### CLI interface boundary

Extracted into:

- [conversation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/conversation.py)
- [errors.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/errors.py)
- [json_output.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/json_output.py)
- [knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/knowledge.py)
- [messages.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/messages.py)
- [notes.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/notes.py)
- [openclaw.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/openclaw.py)
- [personal_management.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal_management.py)
- [personal_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal_logging.py)
- [personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/personal.py)
- [presenters.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/presenters.py)
- [runtime.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/runtime.py)
- [setup.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/setup.py)
- [system.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/system.py)
- [app.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/app.py)
- [commands.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/commands.py)
- [commands_notes.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/commands_notes.py)
- [commands_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/commands_personal.py)
- [commands_core.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/commands_core.py)
- [tables.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/tables.py)

What moved:

- `print_model_json(...)`
- `print_optional_model_json(...)`
- `exit_with_brain_ops_error(...)`
- `capture_result_lines(...)`
- `improve_result_lines(...)`
- `research_result_lines(...)`
- `run_route_input_command(...)`
- `run_handle_input_command(...)`
- `present_route_input_command(...)`
- `present_handle_input_command(...)`
- `run_process_inbox_command(...)`
- `run_weekly_review_command(...)`
- `run_audit_vault_command(...)`
- `run_normalize_frontmatter_command(...)`
- `present_process_inbox_command(...)`
- `present_weekly_review_command(...)`
- `present_audit_vault_command(...)`
- `present_normalize_frontmatter_command(...)`
- `coerce_note_workflow_error(...)`
- `run_capture_command(...)`
- `run_create_note_command(...)`
- `run_create_project_command(...)`
- `run_daily_summary_command(...)`
- `run_improve_note_command(...)`
- `run_research_note_command(...)`
- `run_link_suggestions_command(...)`
- `run_apply_link_suggestions_command(...)`
- `run_promote_note_command(...)`
- `run_enrich_note_command(...)`
- `run_daily_macros_command(...)`
- `run_macro_status_command(...)`
- `run_active_diet_command(...)`
- `run_diet_status_command(...)`
- `run_daily_habits_command(...)`
- `run_habit_status_command(...)`
- `run_body_metrics_status_command(...)`
- `run_workout_status_command(...)`
- `run_spending_summary_command(...)`
- `run_budget_status_command(...)`
- `run_daily_status_command(...)`
- `run_set_macro_targets_command(...)`
- `run_create_diet_plan_command(...)`
- `run_set_active_diet_command(...)`
- `run_update_diet_meal_command(...)`
- `run_set_habit_target_command(...)`
- `run_set_budget_target_command(...)`
- `run_log_meal_command(...)`
- `run_log_supplement_command(...)`
- `run_habit_checkin_command(...)`
- `run_log_body_metrics_command(...)`
- `run_log_workout_command(...)`
- `run_log_expense_command(...)`
- `run_daily_log_command(...)`
- `present_daily_macros_command(...)`
- `present_macro_status_command(...)`
- `present_active_diet_command(...)`
- `present_diet_status_command(...)`
- `present_daily_habits_command(...)`
- `present_habit_status_command(...)`
- `present_body_metrics_status_command(...)`
- `present_workout_status_command(...)`
- `present_spending_summary_command(...)`
- `present_budget_status_command(...)`
- `present_daily_status_command(...)`
- `present_set_macro_targets_command(...)`
- `present_create_diet_plan_command(...)`
- `present_set_active_diet_command(...)`
- `present_update_diet_meal_command(...)`
- `present_set_habit_target_command(...)`
- `present_set_budget_target_command(...)`
- `present_log_meal_command(...)`
- `present_log_supplement_command(...)`
- `present_habit_checkin_command(...)`
- `present_log_body_metrics_command(...)`
- `present_log_workout_command(...)`
- `present_log_expense_command(...)`
- `present_daily_log_command(...)`
- `present_openclaw_manifest(...)`
- `print_handle_input_result(...)`
- `print_operations(...)`
- `print_rendered_with_operations(...)`
- `print_rendered_with_single_operation(...)`
- `print_lines_with_single_operation(...)`
- `print_json_or_rendered(...)`
- `print_optional_json_or_rendered(...)`
- `load_database_path(...)`
- `load_runtime_config(...)`
- `load_validated_vault(...)`
- `initialize_cli_config(...)`
- `present_info_command(...)`
- `present_init_command(...)`
- `present_init_db_command(...)`
- `create_cli_app(...)`
- `register_cli_commands(...)`
- `register_note_and_knowledge_commands(...)`
- `register_personal_commands(...)`
- `register_core_commands(...)`
- `build_operations_table(...)`
- `build_info_table(...)`

Current state:

- reusable CLI JSON output for model-based commands now has an explicit home under `interfaces/cli/`
- reusable CLI error formatting/exit behavior now also has an explicit home under `interfaces/cli/`
- reusable CLI message shaping for note-capture and note-improvement flows now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for conversation-facing commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for vault-maintenance/knowledge commands now also has an explicit home under `interfaces/cli/`
- reusable CLI top-level presentation for conversation and vault-maintenance commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for note-workflow commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for note-creation, project-scaffold, and daily-summary commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for personal summary/status commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for personal target/diet management commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for personal logging/write commands now also has an explicit home under `interfaces/cli/`
- top-level presentation for personal summary/status commands now also has an explicit home under `interfaces/cli/`
- top-level presentation for personal target/diet management commands now also has an explicit home under `interfaces/cli/`
- top-level presentation for personal logging/write commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for `openclaw-manifest` now also has an explicit home under `interfaces/cli/`
- reusable CLI presentation of operations plus rendered results now also has an explicit home under `interfaces/cli/`
- reusable CLI branching between `--json` output and rendered summaries now also has an explicit home under `interfaces/cli/`
- top-level presentation of `handle-input` results now also has an explicit home under `interfaces/cli/`
- reusable CLI resolved database-path loading for sqlite-backed commands now also has an explicit home under `interfaces/cli/`
- reusable CLI config loading for database-backed and routing commands now also has an explicit home under `interfaces/cli/`
- reusable CLI vault-loading and validation for note-oriented commands now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for `init` config creation/structure bootstrap now also has an explicit home under `interfaces/cli/`
- reusable CLI orchestration for `info` and `init-db` now also has an explicit home under `interfaces/cli/`
- CLI app construction now also has an explicit home under `interfaces/cli/`
- top-level composition of all CLI command registrars now also has an explicit home under `interfaces/cli/`
- Typer command registration for the note/knowledge command cluster now also has an explicit home under `interfaces/cli/`
- Typer command registration for the personal command cluster now also has an explicit home under `interfaces/cli/`
- Typer command registration for the core/bootstrap and conversation-facing command cluster now also has an explicit home under `interfaces/cli/`
- reusable CLI table shaping for operations and resolved config info now has an explicit home under `interfaces/cli/`
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) is now effectively a minimal launcher over `create_cli_app(...)`
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) no longer owns inline orchestration for the system/bootstrap cluster (`info`, `init`, `init-db`)
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) no longer owns inline Typer registration for the note/knowledge command cluster either
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) no longer owns inline Typer registration for the personal command cluster either
- [app.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/app.py) now owns final CLI app construction and shared error handling
- [commands.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/commands.py) now owns top-level composition of the `core`, `personal`, and `note/knowledge` command registrars
- consolidation tests now also cover CLI command registration directly in [test_cli_command_registration.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_command_registration.py)
- that registration-level coverage now verifies the core, personal, and note/knowledge registrars both register the expected command names and delegate representative invocations to the correct presenters/error handlers
- that registration-level coverage now also verifies the top-level CLI app factory and aggregate command registrar wire the major command clusters correctly
- consolidation tests now also cover the `system` and `openclaw` CLI adapters directly in [test_cli_system_adapters.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_system_adapters.py)
- that adapter-level coverage now verifies `present_info_command(...)`, `present_init_command(...)`, `present_init_db_command(...)`, and `present_openclaw_manifest(...)` delegate correctly to the new application/system boundary and preserve their expected console behavior
- consolidation tests now also cover representative note-workflow CLI adapters directly in [test_cli_note_adapters.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_note_adapters.py)
- that adapter-level coverage now verifies vault loading, workflow passthrough, and final rendering/presentation wiring for `capture`, `link-suggestions`, `daily-summary`, `promote-note`, and `enrich-note`
- consolidation tests now also cover representative knowledge-maintenance CLI adapters directly in [test_cli_knowledge_adapters.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_knowledge_adapters.py)
- that adapter-level coverage now verifies workflow passthrough and final rendering/presentation wiring for `normalize-frontmatter`, `process-inbox`, `weekly-review`, and `audit-vault`
- consolidation tests now also cover conversation CLI adapters directly in [test_cli_conversation_adapters.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_conversation_adapters.py)
- that adapter-level coverage now verifies workflow passthrough and final rendering/presentation wiring for `route-input` and `handle-input`
- consolidation tests now also cover representative personal CLI adapters directly in [test_cli_personal_adapters.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_cli_personal_adapters.py)
- that adapter-level coverage now verifies workflow passthrough and final rendering/presentation wiring for representative personal status, logging, and management commands

## 2. Core Capabilities Already Extracted

### Execution

Extracted into:

- [runtime.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/core/execution/runtime.py)
- [dispatch.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/core/execution/dispatch.py)

What moved:

- `ExecutionRuntime`
- `IntentExecutionOutcome`
- `build_execution_runtime(...)`
- `build_execution_outcome(...)`
- `execute_intent(...)`

Current state:

- `intent_execution_service.py` still acts as the compatibility adapter and dispatch layer
- reusable execution runtime/result shaping now has an explicit home in `core/execution/`
- top-level intent-execution orchestration now also has an explicit home in `core/execution/`
- a first execution-dispatch slice for operational logging intents now has an explicit home under [intent_execution_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_logging.py)
- a second execution-dispatch slice for personal targets, diet-management, and status intents now has an explicit home under [intent_execution_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_personal.py)
- a third execution-dispatch slice for knowledge capture intents now has an explicit home under [intent_execution_knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_knowledge.py)
- [intent_execution_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_service.py) is now a thin compatibility wrapper over `core/execution/`

### Validation

Extracted into:

- [common.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/core/validation/common.py)
- [db.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/db.py)

What moved:

- `resolve_iso_date(...)`
- `normalize_period(...)`
- `has_any_non_none(...)`
- `resolve_database_path(...)`
- `ensure_database_parent(...)`
- `require_database_file(...)`

Current state:

- repeated ISO-date parsing across services now uses shared validation
- repeated period normalization now uses shared validation
- parser-only structural checks now use `has_any_non_none(...)` in the approved narrow scope
- repeated SQLite database-path expansion, parent-directory creation, and file-existence checks now use shared helpers in `storage/db.py`

Accepted migration note:

- `daily_summary_service.py` now uses shared `resolve_iso_date()`
- behavior is unchanged for valid or missing dates
- invalid dates now raise `ConfigError("Date must be in YYYY-MM-DD format.")` instead of a raw `ValueError`
- this change was accepted for consistency

### Explicit Obsidian storage boundaries

Extracted into:

- [note_paths.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_paths.py)
- [note_templates.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_templates.py)
- [note_loading.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_loading.py)
- [note_inference.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_inference.py)
- [note_listing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_listing.py)
- [note_creation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_creation.py)
- [note_metadata.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_metadata.py)
- [note_writing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/note_writing.py)
- [report_writing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/obsidian/report_writing.py)

What moved:

- `resolve_folder(...)`
- `build_note_path(...)`
- `resolve_note_path(...)`
- `resolve_inbox_destination_path(...)`
- `template_for_note_type(...)`
- `resolve_note_template_path(...)`
- `load_note_document(...)`
- `load_optional_note_document(...)`
- `relative_note_path(...)`
- `infer_note_type_from_relative_path(...)`
- `infer_note_title_from_relative_path(...)`
- `list_vault_markdown_notes(...)`
- `recent_relative_note_paths(...)`
- `build_note_document(...)`
- `read_note_text(...)`
- `apply_note_frontmatter_defaults(...)`
- `apply_note_frontmatter_defaults_with_change(...)`
- `render_note_document(...)`
- `write_note_document(...)`
- `write_report_text(...)`
- `timestamped_report_name(...)`
- `build_in_memory_report_operation(...)`
- `build_report_operation(...)`

Current state:

- folder resolution now has an explicit home under `storage/obsidian/`
- note-path construction from folder/title and note-type/title now also has an explicit home under `storage/obsidian/`
- inbox destination-path resolution from normalized frontmatter now also has an explicit home under `storage/obsidian/`
- template-selection and template-path resolution now have an explicit home under `storage/obsidian/`
- safe note loading plus frontmatter/body parsing now has an explicit home under `storage/obsidian/`
- optional note loading with empty-document fallback now also has an explicit home under `storage/obsidian/`
- relative note-path projection now also has an explicit home under `storage/obsidian/`
- note type/title inference from relative vault paths now has an explicit home under `storage/obsidian/`
- basic frontmatter defaults (`created`, `updated`, `tags`, optional `type`) now have an explicit home under `storage/obsidian/`
- common note write-back from parsed frontmatter/body now has an explicit home under `storage/obsidian/`
- vault-wide and folder-scoped markdown-note listing now has an explicit home under `storage/obsidian/`
- report write semantics for both persisted and in-memory report operations now have an explicit home under `storage/obsidian/`
- generic report-operation shaping now also has an explicit home under `storage/obsidian/`
- [note_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/note_service.py) still owns note creation orchestration

### CLI Reporting

Extracted into:

- [reporting_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/reporting_personal.py)
- [reporting_knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/reporting_knowledge.py)
- [reporting_conversation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/reporting_conversation.py)

What moved:

- `render_meal_log(...)`
- `render_daily_macros(...)`
- `render_macro_targets(...)`
- `render_macro_status(...)`
- `render_diet_plan(...)`
- `render_diet_activation(...)`
- `render_diet_meal_update(...)`
- `render_active_diet(...)`
- `render_diet_status(...)`
- `render_supplement_log(...)`
- `render_habit_checkin(...)`
- `render_habit_target(...)`
- `render_habit_target_status(...)`
- `render_daily_habits(...)`
- `render_body_metrics_log(...)`
- `render_body_metrics_status(...)`
- `render_workout_log(...)`
- `render_workout_status(...)`
- `render_expense_log(...)`
- `render_spending_summary(...)`
- `render_budget_target(...)`
- `render_budget_status(...)`
- `render_daily_log(...)`
- `render_daily_status(...)`

Current state:

- [reporting.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/reporting.py) now keeps general-purpose and knowledge/conversation renderers
- personal CLI-facing renderers now have an explicit home separate from the remaining reporting surface
- knowledge and vault-maintenance CLI-facing renderers now also have an explicit home separate from the remaining reporting surface
- conversation CLI-facing renderers now also have an explicit home separate from the remaining reporting surface
- public reporting imports used by [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) remain stable
- [audit_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/audit_service.py) and [review_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/review_service.py) now consume `reporting_knowledge.py` directly instead of the compatibility facade
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) now also consumes specialized reporting modules directly instead of the compatibility facade
- [reporting.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/reporting.py) is now an explicit compatibility facade with stable re-exports only
- `note_service.py` still owns note creation orchestration and final write orchestration
- `note_service.py` and `inbox_service.py` now reuse shared frontmatter-default handling from `storage/obsidian/`
- `note_service.py`, `daily_summary_service.py`, and `inbox_service.py` now also reuse shared note-path construction from `storage/obsidian/`
- `inbox_service.py` now also reuses shared inbox destination-path resolution from `storage/obsidian/`
- `daily_summary_service.py` now also reuses shared optional note-loading from `storage/obsidian/`
- `inbox_service.py` and `link_service.py` now also reuse shared note-loading/parsing from `storage/obsidian/`
- `promote_service.py` and `normalize_service.py` now also reuse shared frontmatter-default handling from `storage/obsidian/`
- `review_service.py` now also reuses shared note-loading/parsing, and `audit_service.py` now reuses shared safe note-path resolution from `storage/obsidian/`
- `note_service.py`, `inbox_service.py`, and `normalize_service.py` now also reuse shared note write-back from `storage/obsidian/`
- `inbox_service.py` and `normalize_service.py` now also reuse shared note rendering from `storage/obsidian/`
- `audit_service.py`, `review_service.py`, and `normalize_service.py` now also reuse shared markdown-note listing from `storage/obsidian/`
- `inbox_service.py` now also reuses shared folder-scoped markdown-note listing from `storage/obsidian/`
- `audit_service.py`, `normalize_service.py`, and `inbox_service.py` now also reuse shared raw note-text reading from `storage/obsidian/`
- `link_service.py` now also reuses shared markdown-note listing from `storage/obsidian/`
- `audit_service.py` and `review_service.py` now also reuse shared report write-back from `storage/obsidian/`
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) now also reuses shared report write-back for `process-inbox` instead of writing the report inline
- `audit_service.py` and `review_service.py` now also reuse shared in-memory report operation shaping from `storage/obsidian/`
- `review_service.py` and `link_service.py` now also reuse shared relative note-path projection from `storage/obsidian/`
- `link_service.py` now also reuses shared report-operation shaping from `storage/obsidian/`
- `apply_links_service.py`, `research_service.py`, `improve_service.py`, and `promote_service.py` now delegate repeated note load/write concerns plus shared note-path inference concerns to `storage/obsidian/`
- the Obsidian boundary now has six small explicit seams and is at a deliberate pause point

### Explicit SQLite storage boundaries

Extracted into:

- [expenses.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/expenses.py)
- [diets.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/diets.py)
- [goals.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/goals.py)
- [fitness.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/fitness.py)
- [body_metrics.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/body_metrics.py)
- [life_ops.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/life_ops.py)
- [nutrition.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/nutrition.py)
- [daily_summary.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/daily_summary.py)
- [daily_logs.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/daily_logs.py)
- [daily_status.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/storage/sqlite/daily_status.py)

What moved:

- `insert_expense(...)`
- `fetch_expense_category_totals(...)`
- `fetch_expense_summary_header(...)`
- `fetch_active_diet_plan_rows(...)`
- `fetch_actual_meal_progress_rows(...)`
- `fetch_diet_plan_names(...)`
- `activate_diet_plan(...)`
- `create_diet_plan_records(...)`
- `update_active_diet_meal_items(...)`
- `fetch_macro_status_rows(...)`
- `fetch_habit_target_status_rows(...)`
- `upsert_macro_targets(...)`
- `replace_budget_target(...)`
- `upsert_habit_target(...)`
- `fetch_budget_status_rows(...)`
- `insert_workout_log(...)`
- `fetch_workout_status_rows(...)`
- `ensure_body_metrics_schema(...)`
- `ensure_body_metrics_columns(...)`
- `insert_body_metrics_log(...)`
- `fetch_body_metrics_status_rows(...)`
- `fetch_daily_habit_rows(...)`
- `insert_supplement_log(...)`
- `insert_habit_checkin(...)`
- `insert_meal_log(...)`
- `fetch_daily_macro_rows(...)`
- `fetch_daily_summary_supplement_rows(...)`
- `fetch_daily_summary_habit_rows(...)`
- `fetch_daily_summary_daily_log_rows(...)`
- `fetch_daily_summary_body_metric_rows(...)`
- `fetch_daily_summary_expense_rows(...)`
- `fetch_daily_summary_meal_rows(...)`
- `fetch_daily_summary_workout_rows(...)`
- `insert_daily_log(...)`
- `upsert_follow_up(...)`
- `fetch_follow_up_payload(...)`
- `delete_follow_up(...)`
- `fetch_daily_status_local_context(...)`
- `fetch_daily_status_supplement_names(...)`
- `fetch_daily_status_log_count(...)`

Current state:

- `storage/sqlite/` now contains multiple narrow read-only seams plus small validated write seams
- services still own status semantics, validation, normalization, grouping, and result shaping
- SQLite lifecycle cleanup was completed by introducing and rolling out `connect_sqlite(...)`
- the test suite now runs without the previous SQLite `ResourceWarning`

### Conversation-layer seams

Extracted into:

- [results.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/results.py)
- [dispatch.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/dispatch.py)
- [execution.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/execution.py)
- [follow_up.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/follow_up.py)
- [follow_up_input.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/follow_up_input.py)
- [follow_up_state.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/follow_up_state.py)
- [handling.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/handling.py)
- [intake.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/intake.py)
- [parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/parsing.py)
- [parsing_input.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/parsing_input.py)
- [projection.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/projection.py)
- [recommendations.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/recommendations.py)
- [routing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/routing.py)
- [routing_input.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/routing_input.py)
- [splitting.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/splitting.py)

What moved:

- `build_single_intent_result(...)`
- `build_sub_result(...)`
- `build_multi_intent_result(...)`
- `build_failure_result(...)`
- `dispatch_parsed_input(...)`
- `execute_single_intent_result(...)`
- `execute_multi_intent_result(...)`
- `resolve_conversation_input(...)`
- `build_canceled_follow_up_result(...)`
- `build_unresolved_follow_up_result(...)`
- `build_resolved_follow_up_result(...)`
- `apply_pending_follow_up(...)`
- `resolve_follow_up(...)`
- `PendingFollowUp`
- `save_follow_up(...)`
- `load_follow_up(...)`
- `clear_follow_up(...)`
- `active_diet_pending_follow_up(...)`
- `handle_input(...)`
- `should_preserve_single_parse(...)`
- `build_compound_parse_result(...)`
- `parse_intent(...)`
- `parse_intents(...)`
- `display_input_for_intent(...)`
- `format_active_diet_follow_up_message(...)`
- `format_macro_targets_follow_up_message(...)`
- `format_daily_recommendations_message(...)`
- `intent_to_route_decision(...)`
- `route_input(...)`
- `split_compound_input(...)`

Current state:

- conversation-facing result packaging now has an explicit home under `interfaces/conversation/`
- conversation-facing parse-result dispatch now also has an explicit home under `interfaces/conversation/`
- conversation-facing single-intent and multi-intent execution/result preparation now also have an explicit home under `interfaces/conversation/`
- conversation-facing follow-up-or-parse intake resolution now also has an explicit home under `interfaces/conversation/`
- conversation-facing follow-up result construction and pending-follow-up result mutation now also have an explicit home under `interfaces/conversation/`
- conversation-facing follow-up resolution orchestration now also has an explicit home under `interfaces/conversation/`
- conversation-facing pending-follow-up state model, persistence wrapper, and active-diet pending-follow-up construction now also have an explicit home under `interfaces/conversation/`
- top-level conversation input handling orchestration now also has an explicit home under `interfaces/conversation/`
- conversation-facing input projection now also has an explicit home under `interfaces/conversation/`
- conversation-facing compound-input splitting now also has an explicit home under `interfaces/conversation/`
- conversation-facing compound-parse policy and fallback assembly now also have an explicit home under `interfaces/conversation/`
- conversation-facing parser entrypoint orchestration, heuristic acceptance, and LLM arbitration now also have an explicit home under `interfaces/conversation/`
- conversation-facing follow-up recommendation and recap messages now also have an explicit home under `interfaces/conversation/`
- intent-to-route projection now has an explicit home under `interfaces/conversation/`
- top-level heuristic route-input orchestration now also has an explicit home under `interfaces/conversation/`
- [handle_input_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/handle_input_service.py) is now a thin compatibility wrapper over conversation interfaces
- [cli.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/cli.py) now consumes conversation entrypoints directly for `handle_input`, `parse_intent`, and `route_input`, instead of going through service wrappers
- [follow_up_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/follow_up_service.py) is now a thin compatibility wrapper around conversation follow-up state and resolution
- direct wrapper coverage in [test_conversation_compat_wrappers.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_conversation_compat_wrappers.py) now also verifies that the conversation compatibility services still re-export or delegate to the extracted conversation/core entrypoints
- direct heuristic coverage in [test_personal_routing_and_parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_personal_routing_and_parsing.py) now also verifies representative personal routing decisions and logging-intent parsing behavior for macro targets, budget status, habit targets, meals, supplements, habits, body metrics, workouts, and expenses
- direct execution coverage in [test_intent_execution_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_intent_execution_personal.py) now also verifies representative personal intent dispatch for writes, queries, normalized fields, and non-personal fallthrough
- the conversation layer now has a fourth small demotion step beyond result packaging and routing

## 3. Personal Domain Extractions Completed

### Nutrition

Extracted into:

- [meal_parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/nutrition/meal_parsing.py)

What moved:

- `parse_meal_items(...)`
- `_parse_meal_item(...)`
- `_normalize_quantity_words(...)`

Current service adapter:

- [nutrition_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/nutrition_service.py)

What stayed:

- `log_meal(...)`
- `daily_macros(...)`
- SQLite reads/writes
- current service API surface

### Diet

Extracted into:

- [parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/diet/parsing.py)
- [projections.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/diet/projections.py)

What moved:

- `ParsedDietMeal`
- `parse_diet_meal_spec(...)`
- `remaining(...)`
- `build_diet_plan_result(...)`
- `build_diet_activation_result(...)`
- `build_diet_meal_update_result(...)`
- `build_diet_plan_summary(...)`
- `build_diet_status_summary(...)`

Current service adapter:

- [diet_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/diet_service.py)

What stayed:

- `create_diet_plan(...)`
- `set_active_diet(...)`
- `active_diet(...)`
- `update_active_diet_meal(...)`
- `diet_status(...)`
- `load_active_diet_totals(...)`
- SQLite reads/writes
- diet summary assembly from DB rows
- write-result shaping for diet mutations now also lives under [projections.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/diet/projections.py)

### Fitness

Extracted into:

- [workout_parsing.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/fitness/workout_parsing.py)

What moved:

- `parse_workout_entries(...)`
- `_parse_entry(...)`
- supporting regex constants

Current service adapter:

- [fitness_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/fitness_service.py)

What stayed:

- `log_workout(...)`
- `workout_status(...)`
- SQLite reads/writes
- current service API surface

### Daily Status

Extracted into:

- [daily_status.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/daily_status.py)
- [goals.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/goals.py)
- [tracking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/tracking.py)

What moved:

- `build_daily_status_summary(...)`
- `build_macro_targets_result(...)`
- `build_macro_status_summary(...)`
- `build_budget_target_result(...)`
- `build_budget_status_summary(...)`
- `build_habit_target_result(...)`
- `build_habit_target_status_summary(...)`
- `build_spending_summary(...)`
- `build_expense_log_result(...)`
- `build_body_metrics_summary(...)`
- `build_body_metrics_log_result(...)`
- `build_supplement_log_result(...)`
- `build_habit_checkin_result(...)`
- `build_workout_log_result(...)`
- `build_workout_status_summary(...)`
- `build_daily_habits_summary(...)`

Current service adapter:

- [daily_status_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_status_service.py)

What stayed:

- `daily_status(...)`
- cross-capability orchestration
- local supplement/log loading
- compatibility with the current status call graph
- write-result shaping for goals/targets now also lives under [goals.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/goals.py)
- write-result shaping for expense/body-metrics tracking now also lives under [tracking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/tracking.py)
- write-result shaping for supplement and habit check-in logging now also lives under [tracking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/tracking.py)
- write-result shaping for workout logging now also lives under [tracking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/personal/tracking.py)
- consolidation tests now cover representative personal-domain result builders in [test_personal_domain_results.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_personal_domain_results.py)
- that consolidation pass also fixed a real mutability leak in `build_workout_log_result(...)` by deep-copying `WorkoutSetInput` entries before returning the result model
- integration-style consolidation tests now also cover the composed `daily_status(...)` workflow in [test_daily_workflows.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_daily_workflows.py)

## 4. Knowledge Domain Extractions Completed

### Current knowledge-domain modules

The current extracted knowledge modules are:

- [capture.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/capture.py)
  - capture classification
  - capture title inference
  - capture frontmatter shaping
  - capture body shaping

- [linking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/linking.py)
  - link insertion
  - linked-document materialization
  - note-term extraction
  - tokenization
  - existing wikilink extraction
  - lexical scoring heuristics

- [improvement.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/improvement.py)
  - note improvement / reshaping by note type
  - improved-document materialization
  - reusable content-structure rules for knowledge, maps, sources, systems, and projects

- [promotion.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/promotion.py)
  - promotion target defaults
  - promoted title normalization
  - section extraction from note bodies
  - promoted knowledge-body construction
  - related-note backlink insertion semantics

- [research.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/research.py)
  - research block rendering
  - research block merge/replace behavior
  - research document materialization

- [daily_summary.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/daily_summary.py)
  - daily summary note-title formatting
  - daily summary section shaping for meals, workouts, expenses, supplements, habits, body metrics, and daily logs
  - daily summary block rendering
  - daily summary block upsert/materialization
  - daily summary document materialization

- [inbox.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/inbox.py)
  - inbox note-type inference
  - inbox capture-shaped frontmatter enrichment
  - inbox body-structure normalization

- [normalization.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/normalization.py)
  - folder-based default note typing
  - note-type alias normalization
  - systems/maps-specific type normalization
  - tag-string normalization

- [review.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/review.py)
  - stale project-note detection
  - orphan-note detection

- [audit.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/audit.py)
  - audit note-type inference
  - moc detection
  - known note-type catalog
  - system-like note-type catalog

- [enrichment.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/enrichment.py)
  - enrichment step planning
  - enrichment step labeling

### Capture

Extracted into:

- [capture.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/capture.py)

What moved:

- `infer_capture_type(...)`
- `infer_capture_title(...)`
- `build_capture_frontmatter(...)`
- `build_capture_body(...)`
- `plan_capture_note(...)`
- consolidation tests now cover the extracted capture planning seam in [test_knowledge_capture_domain.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_capture_domain.py)
- `_extract_first_url(...)`

Current service adapter:

- [capture_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/capture_service.py)

What stayed:

- `capture_text(...)`
- `Vault` interaction
- `create_note(...)` orchestration
- final `CaptureResult` shaping

### Project Scaffolding

Extracted into:

- [projects.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/projects.py)

What moved:

- `plan_project_scaffold(...)`

Current service adapter:

- [project_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/project_service.py)

What stayed:

- `create_project_scaffold(...)`
- project-name sanitization
- project-folder selection
- note creation orchestration

### Linking

Extracted into:

- [linking.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/linking.py)

What moved first:

- `insert_links(...)`

What moved next:

- `tokenize(...)`
- `existing_wikilinks(...)`
- `build_note_terms(...)`
- `score_terms(...)`
- `suggest_link_candidate(...)`

Current service adapters:

- [apply_links_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/apply_links_service.py)
- [link_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/link_service.py)

What stayed:

- `apply_link_suggestions(...)`
- `suggest_links(...)`
- `_note_terms(...)`
- Vault traversal
- filesystem reads
- candidate note filtering
- service result shaping
- consolidation tests now cover the extracted linking seam in [test_knowledge_linking_domain.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_linking_domain.py)

### Improvement

Extracted into:

- [improvement.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/improvement.py)

What moved:

- `improve_body(...)`
- `improve_knowledge(...)`
- `improve_map(...)`
- `improve_source(...)`
- `improve_system(...)`
- `improve_project(...)`

Current service adapter:

- [improve_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/improve_service.py)

What stayed:

- `improve_note(...)`
- `_infer_type_from_path(...)`
- `_infer_title_from_path(...)`
- Vault path resolution
- file read/write orchestration
- frontmatter update/write behavior
- final `ImproveNoteResult` shaping

### Promotion

Extracted into:

- [promotion.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/promotion.py)

What moved:

- `default_target_type(...)`
- `normalize_promoted_title(...)`
- `extract_sections(...)`
- `ensure_related_note_link(...)`
- `materialize_source_promotion(...)`
- `materialize_stub_promotion(...)`
- consolidation tests now cover the extracted promotion seam in [test_knowledge_promotion_and_inbox.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_promotion_and_inbox.py)

Current service adapter:

- [promote_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/promote_service.py)

What stayed:

- `promote_note(...)`
- `_promote_source_to_knowledge(...)`
- `_promote_stub_to_draft(...)`
- `_infer_type_from_path(...)`
- Vault path resolution
- note creation/update orchestration
- chaining with `improve_note(...)`
- final `PromoteNoteResult` shaping

### Research

Extracted into:

- [research.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/research.py)

What moved:

- `render_research_block(...)`
- `merge_research_block(...)`
- `research_query_candidates(...)`
- `research_search_results(...)`
- `research_summary_text(...)`
- consolidation tests now cover the extracted research seam in [test_knowledge_research_domain.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_research_domain.py)

Current service adapter:

- [research_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/research_service.py)

What stayed:

- `research_note(...)`
- `_fetch_json(...)`
- `_fetch_wikipedia_summary(...)`
- `_search_wikipedia(...)`
- `_search_wikipedia_with_fallback(...)`
- Vault path resolution
- note read/write orchestration
- remote fetch logic
- final `ResearchNoteResult` shaping

### Daily Summary

Extracted into:

- [daily_summary.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/daily_summary.py)

What moved:

- `render_summary_block(...)`
- `upsert_summary_block(...)`

Current service adapter:

- [daily_summary_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_summary_service.py)

What stayed:

- `write_daily_summary(...)`
- SQLite/Vault orchestration
- calls to `diet_status(...)`
- loader coordination
- final `DailySummaryResult` shaping
- integration-style consolidation tests now also cover the composed daily summary note write flow in [test_daily_workflows.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_daily_workflows.py)

### Inbox

Extracted into:

- [inbox.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/inbox.py)

What moved:

- `infer_inbox_note_type(...)`
- `looks_structured(...)`
- `normalize_inbox_note(...)`
- `plan_inbox_disposition(...)`
- consolidation tests now cover the extracted inbox seam in [test_knowledge_promotion_and_inbox.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_promotion_and_inbox.py)

Current service adapter:

- [inbox_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/inbox_service.py)

What stayed:

- `process_inbox(...)`
- single-note load/write/move orchestration
- frontmatter metadata defaults through `storage/obsidian/`
- destination resolution and move decision
- final `InboxItemResult` / `InboxProcessSummary` shaping

### Frontmatter Normalization

Extracted into:

- [normalization.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/normalization.py)

What moved:

- `normalize_note_frontmatter(...)`
- `TYPE_ALIASES`
- `FOLDER_DEFAULTS`

Current service adapter:

- [normalize_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/normalize_service.py)

What stayed:

- `normalize_frontmatter(...)`
- vault traversal
- invalid-frontmatter handling
- frontmatter metadata defaults through `storage/obsidian/`
- final render/write orchestration
- `NormalizeFrontmatterSummary` shaping

### Review

Extracted into:

- [review.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/review.py)

What moved:

- `is_stale_project_note(...)`
- `is_possible_orphan_note(...)`
- `ReviewNoteAnalysis`
- `analyze_review_note(...)`
- `accumulate_review_note(...)`

Current service adapter:

- [review_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/review_service.py)

What stayed:

- `generate_weekly_review(...)`
- vault traversal
- report write orchestration
- `WeeklyReviewSummary` shaping
- consolidation tests now cover the extracted review seam in [test_knowledge_audit_and_review_domain.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_audit_and_review_domain.py)

### Audit

Extracted into:

- [audit.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/audit.py)

What moved:

- `KNOWN_NOTE_TYPES`
- `SYSTEM_LIKE_TYPES`
- `looks_like_moc_note(...)`
- `infer_audit_note_type(...)`
- `AuditNoteAnalysis`
- `analyze_audit_note(...)`
- `accumulate_audit_note(...)`

Current service adapter:

- [audit_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/audit_service.py)

What stayed:

- `audit_vault(...)`
- vault traversal
- invalid frontmatter handling
- folder stats accumulation
- report write orchestration
- `VaultAuditSummary` shaping
- consolidation tests now cover the extracted audit seam in [test_knowledge_audit_and_review_domain.py](/Users/luisencinas/Documents/GitHub/brain-ops/tests/test_knowledge_audit_and_review_domain.py)

### Enrichment

Extracted into:

- [enrichment.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/domains/knowledge/enrichment.py)

What moved:

- `plan_enrichment_steps(...)`
- `describe_improve_step(...)`
- `describe_research_step(...)`
- `describe_apply_links_step(...)`

Current service adapter:

- [enrich_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/enrich_service.py)

What stayed:

- `enrich_note(...)`
- path normalization
- execution of improve/research/apply-links steps
- `EnrichNoteResult` shaping

## 5. Services Still Acting as Compatibility Adapters

The following files still wrap or orchestrate logic that now partially lives in extracted domain/core modules:

- [intent_execution_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_service.py)
- [nutrition_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/nutrition_service.py)
- [diet_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/diet_service.py)
- [fitness_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/fitness_service.py)
- [expenses_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/expenses_service.py)
- [capture_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/capture_service.py)
- [apply_links_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/apply_links_service.py)
- [link_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/link_service.py)
- [improve_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/improve_service.py)
- [promote_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/promote_service.py)
- [research_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/research_service.py)
- [enrich_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/enrich_service.py)
- [note_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/note_service.py)
- [handle_input_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/handle_input_service.py)
- [daily_summary_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_summary_service.py)
- [daily_status_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_status_service.py)

These files still intentionally own:

- SQLite-heavy orchestration
- Vault/file I/O orchestration
- use-case flow assembly
- compatibility with the current call graph

Important current adapter notes:

- [intent_execution_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_service.py) still owns:
  - central compatibility dispatch across parsed intents
  - runtime construction
  - top-level delegation to execution clusters
  - fallback only for unsupported execution paths

- [intent_execution_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_logging.py) now owns:
  - the first coherent execution-dispatch batch for operational logging intents
  - expense, meal, supplement, habit check-in, body metrics, workout, and daily-log outcome preparation

- [intent_execution_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_personal.py) now owns:
  - the second coherent execution-dispatch batch for personal target, diet-management, and status intents
  - macro/budget/habit targets
  - create/set/update diet operations
  - macro/budget/habit/diet/active-diet/daily-status query outcome preparation

- [intent_execution_knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_execution_knowledge.py) now owns:
  - the third coherent execution-dispatch batch for knowledge capture intents
  - capture-note outcome preparation

- [note_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/note_service.py) still owns:
  - template rendering
  - note creation orchestration
  - frontmatter/body assembly
  - `vault.note_path(...)`
  - `vault.write_text(...)`

- [improve_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/improve_service.py) still owns:
  - note improvement semantics
  - final note write orchestration
  - `ImproveNoteResult` shaping

- [apply_links_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/apply_links_service.py) still owns:
  - link-application semantics
  - final note write orchestration
  - `ApplyLinksResult` shaping

- [promote_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/promote_service.py) still owns:
  - promotion path selection
  - source-note update orchestration
  - chaining with `improve_note(...)`
  - `PromoteNoteResult` shaping

- [research_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/research_service.py) still owns:
  - query selection and fallback behavior
  - remote fetch logic
  - note write orchestration
  - `ResearchNoteResult` shaping

- [enrich_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/enrich_service.py) still owns:
  - enrichment orchestration
  - step execution order
  - operation accumulation
  - `EnrichNoteResult` shaping

- [expenses_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/expenses_service.py) still owns:
  - validation
  - currency normalization
  - timestamp defaulting
  - result shaping
  - summary semantics and final `SpendingSummary` shaping

- [diet_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/diet_service.py) still owns:
  - active diet summary/model assembly
  - meal-progress grouping
  - totals accumulation
  - write-path validation and result semantics

- [goals_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/goals_service.py) still owns:
  - active-diet override logic
  - status/business semantics
  - remaining calculations
  - summary assembly
  - period/currency normalization
  - write-path result semantics

- [fitness_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/fitness_service.py) still owns:
  - workout status semantics
  - total/unique-exercise shaping
  - write-path orchestration

- [body_metrics_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/body_metrics_service.py) still owns:
  - body-metrics status semantics
  - latest-value normalization
  - `_ensure_body_metrics_columns(...)`
  - write-path orchestration

- [life_ops_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/life_ops_service.py) still owns:
  - `daily_habits(...)` grouping and summary assembly
  - validation for habits/supplements
  - both write-path result semantics and validation

- [daily_log_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_log_service.py) still owns:
  - payload shaping
  - input validation
  - timestamp defaults
  - `DailyLogResult` shaping

- [daily_summary_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_summary_service.py) still owns:
  - `write_daily_summary(...)` orchestration
  - raw-row loading from SQLite summary helpers
  - daily-note orchestration
  - coordination of note load/write through `storage/obsidian/`
  - `DailySummaryResult` shaping

- [daily_status_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/daily_status_service.py) still owns:
  - `daily_status(...)` composition of multiple status capabilities
  - cross-capability projection of daily state
  - local supplement/log loading around the composed status

- [handle_input_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/handle_input_service.py) still owns:
  - top-level `handle_input(...)` orchestration
  - top-level adapter entrypoint for conversation input
  - the final wrapper around follow-up intake resolution plus parsed-input dispatch

- [intent_parser_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_service.py) still owns:
  - the compatibility wrapper around conversation parsing

## 6. What Has Intentionally NOT Been Moved Yet

### SQLite-heavy logic

Still intentionally left in service-layer files:

- meal writes/reads
- diet writes/reads
- workout writes/reads
- expenses summary semantics beyond the raw fetch helpers
- habits/supplements queries/writes
- daily summary nested shaping, totals, and final use-case orchestration

Reason:

- only narrow raw-row seams have moved so far
- services still intentionally own grouping, normalization, business semantics, and write orchestration

### Vault / file I/O logic

Still intentionally left in service-layer files:

- note creation orchestration
- note improvement orchestration
- note promotion orchestration
- research-note updates
- apply-links note updates
- `vault.note_path(...)`
- `vault.write_text(...)`
- vault path resolution
- filesystem traversal for link suggestions

Reason:

- Obsidian/file handling is still treated as infrastructure/adaptation logic
- only the safe note-loading concern has moved so far for improve/promote flows

### Storage-boundary work still intentionally deferred

Still intentionally left in service-layer files:

- template rendering logic
- broader note creation orchestration
- broader Obsidian/Vault orchestration beyond folder and template resolution
- SQLite-heavy service orchestration beyond the currently approved raw-row seams

Reason:

- small Obsidian and SQLite seams now exist and are validated
- the current strategy is still to move one very small boundary at a time

### Parser / conversation logic

Still intentionally left in the current services:

- `intent_parser_service.py`
- `handle_input_service.py`
- `follow_up_service.py`
- `router_service.py`
- OpenClaw and Telegram-facing orchestration paths
- parser semantics
- intent-building heuristics
- follow-up state handling and follow-up semantic resolution
- orchestration-heavy `handle_input(...)` control flow

Reason:

- conversation is still an adapter layer under migration
- this work has intentionally not moved parser/chat semantics into domain modules
- conversation demotion is still intentionally conservative even after adding `interfaces/conversation/parsing.py`, `interfaces/conversation/parsing_input.py`, `interfaces/conversation/splitting.py`, `interfaces/conversation/projection.py`, `interfaces/conversation/follow_up_input.py`, and follow-up result helpers

### Parser-front heuristics extraction

Recently completed:

- [intent_parser_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_logging.py)
- [intent_parser_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_personal.py)
- [intent_parser_diet.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_diet.py)
- [intent_parser_knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_knowledge.py)

Current status:

- the first coherent intent-builder cluster now lives outside [intent_parser_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_service.py)
- logging-oriented heuristics for:
  - expense
  - meal
  - supplement
  - habit check-in
  - body metrics
  - workout
  now live in `intent_parser_logging.py`
- a second coherent intent-builder cluster now also lives outside [intent_parser_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_service.py)
- personal target/status heuristics for:
  - macro targets
  - budget targets
  - habit targets
  - macro/budget/habit/diet/active-diet/daily-status queries
  now live in `intent_parser_personal.py`
- a third coherent intent-builder cluster now also lives outside [intent_parser_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_service.py)
- diet-management heuristics for:
  - create diet plan
  - set active diet
  - update diet meal
  now live in `intent_parser_diet.py`
- the remaining knowledge-capture builder now also lives outside [intent_parser_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_parser_service.py)
- `CaptureNoteIntent` construction now lives in `intent_parser_knowledge.py`
- top-level parser orchestration now also lives in `interfaces/conversation/parsing_input.py`
- protected-command handling, heuristic acceptance, compound-input handling, parse-failure semantics, and LLM arbitration now also live in `interfaces/conversation/parsing_input.py`
- `interfaces/conversation/intake.py` now depends directly on conversation parsing, not on the parser service wrapper
- `intent_parser_service.py` is now a thin compatibility wrapper over conversation parsing

### Router-front heuristics extraction

Recently completed:

- [router_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_logging.py)
- [router_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_personal.py)
- [router_diet.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_diet.py)
- [router_knowledge.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_knowledge.py)

Current status:

- the first coherent routing-heuristics cluster now lives outside [router_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_service.py)
- logging-oriented routing heuristics for:
  - expense
  - body metrics
  - workout
  - supplement
  - meal
  - habit check-in
  now live in `router_logging.py`
- a second coherent routing-heuristics cluster now also lives outside [router_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_service.py)
- personal target/status routing heuristics for:
  - macro targets
  - budget targets
  - habit targets
  - macro/budget/habit status
  now live in `router_personal.py`
- a third coherent routing-heuristics cluster now also lives outside [router_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_service.py)
- diet routing heuristics for:
  - active diet
  - create diet plan
  - set active diet
  - update diet meal
  - diet status
  now live in `router_diet.py`
- the remaining knowledge/source/project routing heuristics now also live outside [router_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/router_service.py)
- source URL, project capture, and knowledge capture routing now live in `router_knowledge.py`
- top-level routing orchestration plus daily-status/default fallback now also live in `interfaces/conversation/routing_input.py`
- `router_service.py` is now a thin compatibility wrapper over conversation routing

### Conversation formatting extraction

Recently completed:

- [formatting_logging.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/formatting_logging.py)
- [formatting_personal.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/formatting_personal.py)
- [formatting_diet.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/formatting_diet.py)
- [formatting_general.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/formatting_general.py)
- [formatting.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/conversation/formatting.py)

Current status:

- two coherent assistant-message formatting clusters now live outside [intent_formatter_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/intent_formatter_service.py)
- logging-oriented assistant messages for:
  - expense
  - meal
  - supplement
  - habit check-in
  - body metrics
  - workout
  now live in `interfaces/conversation/formatting_logging.py`
- personal assistant messages for:
  - set macro targets
  - set budget target
  - set habit target
  - set active diet
  - macro status
  - budget status
  - habit status
  - active diet
  now live in `interfaces/conversation/formatting_personal.py`
- diet/daily assistant messages for:
  - create diet plan
  - update diet meal
  - diet status
  - daily status
  now live in `interfaces/conversation/formatting_diet.py`
- general assistant messages for:
  - capture note
  - daily log
  now live in `interfaces/conversation/formatting_general.py`
- top-level formatter orchestration and final fallback now also live in `interfaces/conversation/formatting.py`
- `interfaces/conversation/results.py` now depends directly on conversation formatting, not on the formatter service wrapper
- `intent_formatter_service.py` is now a thin compatibility wrapper over conversation formatting

### OpenClaw / CLI interfaces

Still intentionally left as-is:

- CLI entrypoints
- OpenClaw plugin integration
- Telegram-facing routing path through OpenClaw

Reason:

- interface extraction beyond current wrappers is deferred
- preserving behavior is more important than interface reshaping right now

### Other intentionally deferred areas

- storage adapter formalization
- explicit SQLite / Obsidian storage boundary extraction
- events beyond the current minimal extraction
- monitoring domain extraction
- automation/playbooks/runs extraction
- larger second-layer refactors beyond the currently approved slices
- larger conversation-control-flow refactors beyond the currently approved seams

## 7. Next Likely Migration Directions

### Conversation demotion pause

Recently completed:

- `interfaces/conversation/results.py`
- `interfaces/conversation/dispatch.py`
- `interfaces/conversation/execution.py`
- `interfaces/conversation/follow_up.py`
- `interfaces/conversation/intake.py`
- `interfaces/conversation/projection.py`
- `interfaces/conversation/routing.py`

Current status:

- the conversation layer now has explicit seams for follow-up-or-parse intake resolution, parse-result dispatch, result packaging, execution/result preparation, follow-up result construction, input projection, pending-follow-up result mutation, and intent-to-route projection
- [handle_input_service.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/services/handle_input_service.py) still remains the orchestration layer
- the next likely conversation step is no longer packaging, intake, dispatch, execution/result preparation, or follow-up result construction, but a much more deliberate orchestration decision about whether `handle_input_service.py` and `follow_up_service.py` should stay as the final adapter wrappers

### SQLite seam front

Recently completed:

- `storage/sqlite/expenses.py`
- `storage/sqlite/diets.py`
- `storage/sqlite/goals.py`
- `storage/sqlite/fitness.py`
- `storage/sqlite/body_metrics.py`
- `storage/sqlite/life_ops.py`
- `storage/sqlite/daily_summary.py`
- `storage/sqlite/daily_logs.py`
- `storage/sqlite/daily_status.py`

Current status:

- the narrow raw-row seam pattern is now validated in multiple services
- small write-path seams are now also validated in multiple services
- services remain compatibility adapters and status builders
- the SQLite lifecycle cleanup is complete and no longer the active front
- `goals_service.py` now has consistent read and write seams for macro, budget, and habit flows
- `fitness_service.py` now delegates both workout status reads and workout log writes
- `body_metrics_service.py` now delegates both body-metrics status reads and body-metrics log writes while still owning status shaping
- `nutrition_service.py` now delegates both meal-log writes and daily-macro reads while still owning parsing and result shaping
- `diet_service.py` now delegates its plan writes and read paths while still owning parsing, grouping, totals, and result semantics

### Knowledge follow-up

Recently completed:

- `capture.py`
- `linking.py`
- `improvement.py`
- `promotion.py`
- `research.py`
- `daily_summary.py`
- `enrichment.py`

Current status:

- knowledge-domain extraction now also includes daily-summary title, full section shaping, and block/document materialization semantics
- knowledge-domain extraction now also includes reusable document materialization for linking, improvement, promotion, and research flows
- knowledge-domain extraction now also includes the first reusable enrichment composition seam
- `daily_summary_service.py` remains the orchestration layer for data loading and note writing while delegating daily-summary title, shaping, and content materialization
- `enrich_service.py` remains the orchestration layer for running the enrichment pipeline

### Storage boundary work

Possible future direction:

- continue making Obsidian boundaries more explicit under `storage/obsidian/`

Not yet recommended as the immediate next step because:

- the next move still needs to stay extremely small and safe
- `storage/sqlite/` now has enough critical mass that the next frontier does not need to be another SQLite micro-seam

### Obsidian/Vault seam front

Recently completed:

- `storage/obsidian/note_paths.py`
- `storage/obsidian/note_templates.py`
- `storage/obsidian/note_loading.py`
- `storage/obsidian/note_inference.py`
- `storage/obsidian/note_metadata.py`
- `storage/obsidian/note_writing.py`

Current status:

- `note_service.py` delegates folder, template, and frontmatter-default concerns
- `inbox_service.py` delegates shared frontmatter-default concerns
- `apply_links_service.py`, `research_service.py`, `improve_service.py`, and `promote_service.py` delegate repeated note load/write plus shared note-path inference concerns
- knowledge workflows now consistently follow the pattern: service orchestrates, domain materializes content/document shape, storage handles shared note load/write
- the next move in this front is no longer an obvious micro-seam and should be reassessed before more code changes

### Likely next front

Most likely next architectural front:

- pause here and do a fresh global reassessment before opening another major front

Why:

- `daily_summary_service.py` / `daily_status_service.py` and the Obsidian note-update flows now already have initial seams in place
- continuing immediately in any one of those fronts would risk over-fragmenting composed SmartHub use cases
- the next step should be chosen deliberately across the whole repo, not by inertia inside the current front

### Deferred personal domains

Likely later, if justified:

- `expenses_service.py`
- `life_ops_service.py`
- `daily_log_service.py`

Current judgment:

- `goals_service.py` now has valid read and write SQLite seams
- `fitness_service.py` now has valid read and write SQLite seams
- `body_metrics_service.py` now has valid read and write SQLite seams
- `nutrition_service.py` now has valid read and write SQLite seams
- `diet_service.py` now has valid read and write SQLite seams, including the larger plan-creation path
- `daily_log_service.py` now has a valid first write seam

- `life_ops_service.py` now has valid first read-only and write SQLite seams
- the remaining broader personal-service write paths are now concentrated mainly in a few composed status/use-case flows rather than the simpler personal services

## Practical Note

All extraction steps above were done under these rules:

- no change to public service signatures
- no movement of SQLite-heavy logic
- no movement of Vault/filesystem logic
- no parser / CLI / OpenClaw refactor in the same step
- compile and test verification after each slice

## Recent consolidation

- Added direct coverage for `services/intent_execution_logging.py` and `services/router_logging.py` in `tests/test_logging_execution_and_routing.py`, validating representative logging intent execution and logging-route heuristics.
- Added direct coverage for `services/router_knowledge.py`, `services/intent_parser_knowledge.py`, and `services/intent_execution_knowledge.py` in `tests/test_knowledge_execution_and_routing.py`, validating representative knowledge routing, parsing, and capture execution flow.
- Added direct coverage for `services/router_diet.py` and `services/intent_parser_diet.py` in `tests/test_diet_routing_and_parsing.py`, validating representative diet routing heuristics and natural-language diet intent parsing.
- Added direct coverage for `interfaces/conversation/routing_input.py` and `interfaces/conversation/parsing_input.py` in `tests/test_conversation_routing_and_parsing_inputs.py`, validating router precedence, heuristic fallback, LLM arbitration, and compound-input parsing across domains.
- Added direct coverage for `interfaces/conversation/execution.py` and `core/execution/dispatch.py` in `tests/test_conversation_execution_and_dispatch.py`, validating single-intent follow-up flow, multi-intent aggregation, and execution-dispatch precedence.
- Added direct coverage for `interfaces/conversation/intake.py`, `interfaces/conversation/follow_up_input.py`, and `interfaces/conversation/handling.py` in `tests/test_conversation_handling_and_follow_up.py`, validating follow-up-first intake, handle-input dispatching, and resolved/canceled/unresolved follow-up branches.
- Added direct coverage for `storage/db.py` and `core/validation/common.py` in `tests/test_storage_db_and_validation.py`, validating SQLite lifecycle helpers, schema initialization, and shared validation utilities.
- Added direct coverage for `storage/obsidian/note_loading.py`, `storage/obsidian/note_paths.py`, and `storage/obsidian/report_writing.py` in `tests/test_obsidian_boundaries.py`, validating note-path resolution, note document loading, inbox destination resolution, and report-writing helpers with a real temporary vault.
- Added direct coverage for the remaining compatibility surfaces in `tests/test_reporting_facade_and_cli_app.py`, validating `reporting.py` re-exports and `interfaces/cli/app.py` app construction plus shared error-handler wiring.
- Added direct coverage for the new public export surfaces in `tests/test_public_export_surfaces.py`, validating stable `__all__` contracts and representative re-exports across `application`, `interfaces/cli`, `interfaces/conversation`, `storage/obsidian`, and `storage/sqlite`.
- Normalized the remaining conversation compatibility wrappers in `services/` into explicit façade modules with stable docstrings and `__all__` exports, without changing behavior.
- Verified that the remaining conversation compatibility wrappers and `reporting.py` no longer have internal production consumers in `src/`; they are now documented as deprecated compatibility surfaces retained for stable imports and staged external migration.
- Migrated `tests/test_intent_pipeline.py` from conversation compatibility wrappers to the extracted conversation interface modules directly, leaving the legacy wrappers exercised only by explicit compatibility tests.
- Added `tests/test_legacy_surface_boundaries.py` to guard that `src/` does not regress into importing deprecated conversation compatibility wrappers or the deprecated `reporting.py` facade.
- Extended `tests/test_legacy_surface_boundaries.py` so that deprecated conversation wrappers and the deprecated `reporting.py` facade are only allowed in their explicit compatibility test suites, not in general tests.
- Opened `core/events/` as a real minimal internal boundary with `DomainEvent`, event construction helpers, sink protocol/no-op/collecting sinks, and direct coverage in `tests/test_core_events.py`.
- Integrated the first real event emission path at the `application/notes.py` boundary, publishing operation-derived events via optional event sinks without changing workflow return contracts.
- Extended the same event-emission pattern to `application/knowledge.py`, so stable knowledge-maintenance workflows can also publish operation-derived events through optional event sinks without changing return contracts.
- Extracted the shared publication logic to `application/events.py`, so `application/notes.py` and `application/knowledge.py` now reuse one event-publication helper before expanding the pattern further.
- Extended the same optional event-sink pattern to write workflows in `application/personal.py`, so logging and target-management operations can emit operation-derived events while read-only personal queries remain unchanged.
- Extended the same optional event-sink pattern to `application/system.py` for `init` and `init-db`, so bootstrap workflows that already return `OperationRecord` lists can publish operation-derived events without changing their return contracts; `info` and `openclaw-manifest` remain read-only/path-only workflows.
- Extended the same optional event-sink pattern to `application/conversation.py` for `handle-input`, so top-level conversational execution can publish operation-derived events from aggregated `HandleInputResult.operations` without changing routing behavior or return contracts.
- Added the first reusable persistent event sink in `core/events` via `JsonlFileEventSink`, plus `interfaces/cli/runtime.py::load_event_sink()` backed by `BRAIN_OPS_EVENT_LOG`; `interfaces/cli/conversation.py` now passes that sink into `handle-input`, making event emission consumable from the CLI without coupling instrumentation to presentation.
- Extended the same CLI-level event-sink wiring to `interfaces/cli/notes.py`, so note workflows now pass the opt-in `BRAIN_OPS_EVENT_LOG` sink into `application/notes.py` without changing command presentation behavior.
- Extended the same CLI-level event-sink wiring to `interfaces/cli/knowledge.py`, so maintenance workflows now also pass the opt-in `BRAIN_OPS_EVENT_LOG` sink into `application/knowledge.py` without changing command presentation behavior.
- Extended the same CLI-level event-sink wiring to `interfaces/cli/personal_logging.py`, so personal logging commands now also pass the opt-in `BRAIN_OPS_EVENT_LOG` sink into `application/personal.py` without changing command presentation behavior.
- Extended the same CLI-level event-sink wiring to `interfaces/cli/personal_management.py`, so personal target and diet-management commands now also pass the opt-in `BRAIN_OPS_EVENT_LOG` sink into `application/personal.py` without changing command presentation behavior.
- Extended the same CLI-level event-sink wiring to `interfaces/cli/system.py` for `init` and `init-db`, so bootstrap commands now also pass the opt-in `BRAIN_OPS_EVENT_LOG` sink into `application/system.py` without changing command presentation behavior.
- Added direct integration-style coverage in `tests/test_cli_event_sink_wiring.py`, validating that representative CLI adapters across conversation, notes, knowledge, personal logging, personal management, and system actually construct a `JsonlFileEventSink` from `BRAIN_OPS_EVENT_LOG` and pass it into the application boundary.
- Opened the first real monitoring/observability consumption path on top of events: `core/events/reading.py` now reads and summarizes JSONL event logs, `application/monitoring.py` exposes a reusable summary workflow, and `interfaces/cli/monitoring.py` plus the new `event-log-summary` core command make the event log directly inspectable from the CLI.
- Enriched `event-log-summary` with workflow-level aggregation derived from event payloads, so the first monitoring slice now surfaces not only event names and sources but also the most common emitting workflows.
- Extended the same monitoring slice with optional exact `source` filtering in both `event-log-summary` and `event-log-tail`, making the event log immediately usable for focused inspection of `application.notes`, `application.knowledge`, `application.personal`, and similar boundaries.
- Extended the same monitoring slice with optional exact `workflow` filtering in both `event-log-summary` and `event-log-tail`, so event inspection can now target concrete emitting workflows such as `capture`, `process-inbox`, `handle-input`, or `create-diet-plan` instead of only coarse source boundaries.
- Enriched `event-log-summary` again with daily aggregation, so the first monitoring slice now exposes basic trend shape over time instead of only raw counts by name, source, and workflow.
- Added `event-log-report` as the first composed observability surface over the event log: one command now combines filtered summary plus recent events in a single report, instead of requiring separate summary and tail calls.
- Enriched the event-log summary/report slice with operation-level aggregation from event payloads, so monitoring now surfaces top `action` and `status` values in addition to names, sources, workflows, and days.
- Extended the same monitoring slice with optional exact `status` filtering in `event-log-summary`, `event-log-tail`, and `event-log-report`, so event inspection can isolate only `created`, `updated`, `moved`, `reported`, and similar operation outcomes.
- Enriched the same monitoring slice with `path` aggregation from event payloads, so summary/report views now surface the most frequently touched notes/files without requiring manual inspection of the recent-event tail.
- Enriched the same monitoring slice with `outcome` aggregation (`action:status`) from event payloads, so summary/report views now surface the dominant kinds of work being performed instead of forcing readers to mentally combine separate action and status lists.
- Extended the same monitoring slice with optional exact `until` filtering in `event-log-summary`, `event-log-tail`, and `event-log-report`, so event inspection now supports closed time windows instead of only open-ended `since` filtering.
- Enriched `event-log-report` with a composed `daily_activity` view, so the observability report now includes per-day totals plus top sources/workflows/outcomes instead of only global aggregates and a raw recent-event tail.
- Enriched `event-log-report` again with `highlights`, so the report now surfaces an executive focus block (latest active day, latest top source/workflow/outcome, and top touched path) before the more detailed daily/tail sections.
- Added `event-log-hotspots` as a focused observability surface over the same event slice, exposing the hottest sources, workflows, outcomes, and touched paths without requiring the full summary/report payload.
- Added `event-log-failures` as the first attention-oriented observability surface, isolating skipped/failed/error-like events into a dedicated summary-plus-tail view instead of forcing operators to infer them from general-purpose reports.
- Added `event-log-alerts` as the first composed attention report over the event slice, combining filtered failure/skip summary, daily attention activity, highlights, and recent attention events in one CLI surface.
- Added `event-log-alert-check` as the first threshold-based evaluation surface over attention events, turning observability into a simple actionable pass/fail check instead of only descriptive reporting.
- Extracted a reusable `EventLogAlertPolicy` / `build_event_log_alert_policy(...)` shape in `application/monitoring.py`, so alert evaluation no longer depends on ad-hoc threshold arguments and can grow into richer alerting policy later.
- Added `event-log-alert-presets` plus public exports for the named alert policies, so the reusable monitoring policy is now discoverable from CLI and stable as a public application/adapter contract instead of only existing as internal plumbing.
- Opened the first minimal `alerts` application slice on top of monitoring with an actionable `AlertMessage` plus `event-log-alert-message`, so alert evaluation can now produce a reusable notification-style payload instead of only checks, reports, and tables.
- Opened the first minimal `automation` slice on top of alerts with `AlertDelivery` plus `event-log-alert-deliver`, so the monitoring/alerts stack can now hand off alert artifacts to files in a reusable way instead of stopping at in-memory messages and CLI-only rendering.
- Extended that automation slice with a reusable `AlertDeliveryPolicy` and default output resolution (`BRAIN_OPS_ALERT_OUTPUT_DIR` or a sibling `alerts/` directory next to the event log), so delivery can now work as a real policy-driven capability instead of requiring a fully manual `--output` path every time.
- Extended that delivery policy with a stable `latest` artifact alongside the derived per-run file, so external consumers now have both a descriptive path and a fixed handoff path that does not require rediscovering the generated filename.
- Extended that delivery policy with explicit `delivery_mode` handling (`both`, `archive`, `latest`), so automation can now choose between historical artifacts, a stable handoff path, or both without changing the alert-evaluation workflow itself.
- Consolidated the `event-log-alert-deliver` CLI surface so `interfaces/cli/monitoring.py` now reuses the specialized adapter in [automation.py](/Users/luisencinas/Documents/GitHub/brain-ops/src/brain_ops/interfaces/cli/automation.py) instead of carrying a second inline implementation, removing a real duplication point that had already caused drift.
- Made the delivery `target` explicit in `AlertDeliveryPolicy` and `event-log-alert-deliver`, even though `file` is still the only supported target today, so the automation slice now has a clearer dispatch boundary for future delivery backends instead of mixing destination semantics into file-only helpers.
- Opened the second real delivery target, `stdout`, so `event-log-alert-deliver` can now be used directly in shell pipelines and lightweight automation without always writing a file artifact first.
