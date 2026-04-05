from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.core.events import CollectingEventSink
from brain_ops.application.conversation import (
    execute_handle_input_workflow,
    execute_route_input_workflow,
)
from brain_ops.application.monitoring import execute_event_log_summary_workflow, execute_event_log_tail_workflow
from brain_ops.application.knowledge import (
    execute_audit_vault_workflow,
    execute_normalize_frontmatter_workflow,
    execute_process_inbox_workflow,
    execute_weekly_review_workflow,
)
from brain_ops.application.notes import (
    execute_apply_link_suggestions_workflow,
    execute_capture_workflow,
    execute_create_project_workflow,
    execute_create_note_workflow,
    execute_daily_summary_workflow,
    execute_enrich_note_workflow,
    execute_improve_note_workflow,
    execute_link_suggestions_workflow,
    execute_promote_note_workflow,
    execute_research_note_workflow,
)
from brain_ops.application.personal import (
    execute_create_diet_plan_workflow,
    execute_log_body_metrics_workflow,
    execute_log_expense_workflow,
    execute_set_budget_target_workflow,
    execute_spending_summary_workflow,
)
from brain_ops.application.system import (
    execute_info_workflow,
    execute_init_db_workflow,
    execute_init_workflow,
    execute_openclaw_manifest_workflow,
)
from brain_ops.config import VaultConfig
from brain_ops.errors import ConfigError
from brain_ops.intents import ParseFailure
from brain_ops.models import OperationRecord, OperationStatus


class ApplicationWorkflowsTestCase(TestCase):
    def test_event_log_summary_workflow_loads_path_then_summarizes(self) -> None:
        summary = object()
        summarize_log = patch(
            "brain_ops.application.monitoring.summarize_event_log",
            return_value=summary,
        ).start()
        self.addCleanup(patch.stopall)
        result = execute_event_log_summary_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=7,
            source="application.notes",
            workflow="capture",
            status="created",
            since="2026-04-04",
            until="2026-04-05",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            summarize_log=summarize_log,
        )

        self.assertIs(result, summary)
        summarize_log.assert_called_once_with(
            Path("/tmp/events.jsonl"),
            top=7,
            source="application.notes",
            workflow="capture",
            status="created",
            since="parsed:2026-04-04",
            until="parsed:2026-04-05",
        )

    def test_event_log_tail_workflow_loads_path_then_tails(self) -> None:
        events = [object(), object()]
        tail_log = patch(
            "brain_ops.application.monitoring.tail_event_log",
            return_value=events,
        ).start()
        self.addCleanup(patch.stopall)
        result = execute_event_log_tail_workflow(
            event_log_path=Path("~/events.jsonl"),
            limit=4,
            source="application.personal",
            workflow="log-expense",
            status="updated",
            since="2026-04-04T10:00:00+00:00",
            until="2026-04-04T12:00:00+00:00",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            tail_log=tail_log,
        )

        self.assertIs(result, events)
        tail_log.assert_called_once_with(
            Path("/tmp/events.jsonl"),
            limit=4,
            source="application.personal",
            workflow="log-expense",
            status="updated",
            since="parsed:2026-04-04T10:00:00+00:00",
            until="parsed:2026-04-04T12:00:00+00:00",
        )

    def test_route_input_workflow_reuses_heuristic_result_on_parse_failure(self) -> None:
        heuristic = SimpleNamespace(routing_source="heuristic", reason="heuristic reason")
        failure = ParseFailure(
            input_text="texto",
            reason="llm parse failure",
            routing_source="llm_fallback",
        )

        with (
            patch("brain_ops.application.conversation.route_input", return_value=heuristic) as route_mock,
            patch("brain_ops.application.conversation.parse_intent", return_value=failure) as parse_mock,
        ):
            config = object()
            result = execute_route_input_workflow(
                config_path=Path("/tmp/config.yml"),
                text="texto",
                use_llm=True,
                load_config=lambda _: config,
            )

        self.assertIs(result, heuristic)
        self.assertEqual(result.routing_source, "llm_fallback")
        self.assertEqual(result.reason, "llm parse failure")
        route_mock.assert_called_once_with("texto")
        parse_mock.assert_called_once_with(config, "texto", use_llm=True)

    def test_route_input_workflow_returns_decision_for_parsed_intent(self) -> None:
        parsed_intent = SimpleNamespace(command="daily-status")
        route_decision = SimpleNamespace(command="daily-status", routing_source="intent")

        with (
            patch("brain_ops.application.conversation.route_input") as route_mock,
            patch("brain_ops.application.conversation.parse_intent", return_value=parsed_intent) as parse_mock,
            patch(
                "brain_ops.application.conversation.intent_to_route_decision",
                return_value=route_decision,
            ) as decision_mock,
        ):
            config = object()
            result = execute_route_input_workflow(
                config_path=None,
                text="como voy hoy",
                use_llm=False,
                load_config=lambda _: config,
            )

        self.assertIs(result, route_decision)
        route_mock.assert_called_once_with("como voy hoy")
        parse_mock.assert_called_once_with(config, "como voy hoy", use_llm=False)
        decision_mock.assert_called_once_with(parsed_intent, "como voy hoy")

    def test_handle_input_workflow_loads_config_and_delegates(self) -> None:
        expected = SimpleNamespace(message="ok")
        config = object()

        with patch("brain_ops.application.conversation.handle_input", return_value=expected) as handle_mock:
            result = execute_handle_input_workflow(
                config_path=Path("/tmp/config.yml"),
                text="registra desayuno",
                dry_run=True,
                use_llm=None,
                session_id="session-1",
                load_config=lambda _: config,
            )

        self.assertIs(result, expected)
        handle_mock.assert_called_once_with(
            config,
            "registra desayuno",
            dry_run=True,
            use_llm=None,
            session_id="session-1",
        )

    def test_handle_input_workflow_publishes_events_from_operations(self) -> None:
        operation = OperationRecord(
            action="log meal",
            path=Path("/tmp/brain_ops.sqlite"),
            detail="Meal logged",
            status=OperationStatus.CREATED,
        )
        expected = SimpleNamespace(operations=[operation])
        sink = CollectingEventSink()
        config = object()

        with patch("brain_ops.application.conversation.handle_input", return_value=expected) as handle_mock:
            result = execute_handle_input_workflow(
                config_path=Path("/tmp/config.yml"),
                text="registra desayuno",
                dry_run=False,
                use_llm=True,
                session_id="session-1",
                load_config=lambda _: config,
                event_sink=sink,
            )

        self.assertIs(result, expected)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.conversation")
        self.assertEqual(sink.events[0].payload["workflow"], "handle-input")
        handle_mock.assert_called_once_with(
            config,
            "registra desayuno",
            dry_run=False,
            use_llm=True,
            session_id="session-1",
        )

    def test_process_inbox_workflow_appends_report_operation_when_enabled(self) -> None:
        summary = SimpleNamespace(operations=[])
        report_operation = OperationRecord(
            action="write report",
            path=Path("Reports/inbox-report.md"),
            detail="Inbox processing report",
            status=OperationStatus.REPORT,
        )
        vault = object()

        with (
            patch("brain_ops.application.knowledge.process_inbox", return_value=summary) as process_mock,
            patch("brain_ops.application.knowledge.render_inbox_report", return_value="report body") as render_mock,
            patch(
                "brain_ops.application.knowledge.write_report_text",
                return_value=report_operation,
            ) as write_report_mock,
        ):
            result = execute_process_inbox_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                write_report=True,
                improve_structure=False,
                load_vault=lambda *_args, **_kwargs: vault,
            )

        self.assertIs(result, summary)
        self.assertEqual(summary.operations, [report_operation])
        process_mock.assert_called_once_with(vault, improve_structure=False)
        render_mock.assert_called_once_with(summary)
        write_report_mock.assert_called_once()

    def test_process_inbox_workflow_publishes_events_from_operations(self) -> None:
        operation = OperationRecord(
            action="move note",
            path=Path("Sources/Idea.md"),
            detail="Moved from inbox",
            status=OperationStatus.MOVED,
        )
        summary = SimpleNamespace(operations=[operation])
        sink = CollectingEventSink()
        vault = object()

        with patch("brain_ops.application.knowledge.process_inbox", return_value=summary):
            result = execute_process_inbox_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                write_report=False,
                improve_structure=False,
                load_vault=lambda *_args, **_kwargs: vault,
                event_sink=sink,
            )

        self.assertIs(result, summary)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.moved")
        self.assertEqual(sink.events[0].source, "application.knowledge")
        self.assertEqual(sink.events[0].payload["workflow"], "process-inbox")
        self.assertEqual(sink.events[0].payload["path"], "Sources/Idea.md")

    def test_normalize_frontmatter_workflow_uses_dry_run_vault_loader(self) -> None:
        summary = SimpleNamespace(updated=3)
        loader_calls: list[tuple[Path | None, bool]] = []
        vault = object()

        def load_vault(config_path: Path | None, *, dry_run: bool):
            loader_calls.append((config_path, dry_run))
            return vault

        with patch("brain_ops.application.knowledge.normalize_frontmatter", return_value=summary) as normalize_mock:
            result = execute_normalize_frontmatter_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                load_vault=load_vault,
            )

        self.assertIs(result, summary)
        self.assertEqual(loader_calls, [(Path("/tmp/config.yml"), True)])
        normalize_mock.assert_called_once_with(vault)

    def test_weekly_review_workflow_passes_stale_days_and_write_report(self) -> None:
        summary = SimpleNamespace(generated=True)
        vault = object()
        loader_calls: list[tuple[Path | None, bool]] = []

        def load_vault(config_path: Path | None, *, dry_run: bool):
            loader_calls.append((config_path, dry_run))
            return vault

        with patch("brain_ops.application.knowledge.generate_weekly_review", return_value=summary) as review_mock:
            result = execute_weekly_review_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                stale_days=14,
                write_report=True,
                load_vault=load_vault,
            )

        self.assertIs(result, summary)
        self.assertEqual(loader_calls, [(Path("/tmp/config.yml"), True)])
        review_mock.assert_called_once_with(vault, stale_days=14, write_report=True)

    def test_audit_vault_workflow_uses_non_dry_run_loader(self) -> None:
        summary = SimpleNamespace(audited=True)
        vault = object()
        loader_calls: list[tuple[Path | None, bool]] = []

        def load_vault(config_path: Path | None, *, dry_run: bool):
            loader_calls.append((config_path, dry_run))
            return vault

        with patch("brain_ops.application.knowledge.audit_vault", return_value=summary) as audit_mock:
            result = execute_audit_vault_workflow(
                config_path=Path("/tmp/config.yml"),
                write_report=True,
                load_vault=load_vault,
            )

        self.assertIs(result, summary)
        self.assertEqual(loader_calls, [(Path("/tmp/config.yml"), False)])
        audit_mock.assert_called_once_with(vault, write_report=True)

    def test_audit_vault_workflow_publishes_report_event_when_sink_provided(self) -> None:
        operation = OperationRecord(
            action="write report",
            path=Path("Reports/audit.md"),
            detail="Vault audit report",
            status=OperationStatus.REPORT,
        )
        summary = SimpleNamespace(operations=[operation])
        sink = CollectingEventSink()
        vault = object()

        with patch("brain_ops.application.knowledge.audit_vault", return_value=summary):
            result = execute_audit_vault_workflow(
                config_path=Path("/tmp/config.yml"),
                write_report=True,
                load_vault=lambda *_args, **_kwargs: vault,
                event_sink=sink,
            )

        self.assertIs(result, summary)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.report")
        self.assertEqual(sink.events[0].payload["workflow"], "audit-vault")
        self.assertEqual(sink.events[0].payload["path"], "Reports/audit.md")

    def test_log_body_metrics_workflow_parses_iso_datetime(self) -> None:
        expected = SimpleNamespace(reason="logged")

        with patch("brain_ops.application.personal.log_body_metrics", return_value=expected) as log_mock:
            result = execute_log_body_metrics_workflow(
                config_path=Path("/tmp/config.yml"),
                weight_kg=80.5,
                body_fat_pct=14.2,
                fat_mass_kg=None,
                muscle_mass_kg=None,
                visceral_fat=None,
                bmr_calories=None,
                arm_cm=None,
                waist_cm=None,
                thigh_cm=None,
                calf_cm=None,
                logged_at="2026-04-04T08:30:00",
                note="morning check",
                dry_run=False,
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
            )

        self.assertIs(result, expected)
        self.assertEqual(log_mock.call_args.args[0], Path("/tmp/brain_ops.sqlite"))
        self.assertEqual(
            log_mock.call_args.kwargs["logged_at"],
            datetime(2026, 4, 4, 8, 30, 0),
        )
        self.assertEqual(log_mock.call_args.kwargs["note"], "morning check")
        self.assertFalse(log_mock.call_args.kwargs["dry_run"])

    def test_spending_summary_workflow_passes_currency_and_date(self) -> None:
        expected = SimpleNamespace(total=150)

        with patch("brain_ops.application.personal.spending_summary", return_value=expected) as spending_mock:
            result = execute_spending_summary_workflow(
                config_path=Path("/tmp/config.yml"),
                date="2026-04-04",
                currency="USD",
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
            )

        self.assertIs(result, expected)
        spending_mock.assert_called_once_with(
            Path("/tmp/brain_ops.sqlite"),
            date_text="2026-04-04",
            currency="USD",
        )

    def test_log_expense_workflow_publishes_operation_event_when_sink_provided(self) -> None:
        operation = OperationRecord(
            action="log expense",
            path=Path("/tmp/brain_ops.sqlite"),
            detail="Expense logged",
            status=OperationStatus.CREATED,
        )
        expected = SimpleNamespace(operation=operation)
        sink = CollectingEventSink()

        with patch("brain_ops.application.personal.log_expense", return_value=expected) as expense_mock:
            result = execute_log_expense_workflow(
                config_path=Path("/tmp/config.yml"),
                amount=25.0,
                category="food",
                merchant="Cafe",
                currency="USD",
                note="lunch",
                dry_run=False,
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
                event_sink=sink,
            )

        self.assertIs(result, expected)
        expense_mock.assert_called_once()
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.personal")
        self.assertEqual(sink.events[0].payload["workflow"], "log-expense")

    def test_set_budget_target_workflow_preserves_optional_category(self) -> None:
        expected = SimpleNamespace(reason="budget updated")

        with patch("brain_ops.application.personal.set_budget_target", return_value=expected) as budget_mock:
            result = execute_set_budget_target_workflow(
                config_path=Path("/tmp/config.yml"),
                amount=5000,
                period="monthly",
                category="food",
                currency="MXN",
                dry_run=True,
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
            )

        self.assertIs(result, expected)
        budget_mock.assert_called_once_with(
            Path("/tmp/brain_ops.sqlite"),
            amount=5000,
            period="monthly",
            category="food",
            currency="MXN",
            dry_run=True,
        )

    def test_create_diet_plan_workflow_maps_meal_argument_to_service_meals(self) -> None:
        expected = SimpleNamespace(reason="diet created")

        with patch("brain_ops.application.personal.create_diet_plan", return_value=expected) as diet_mock:
            result = execute_create_diet_plan_workflow(
                config_path=Path("/tmp/config.yml"),
                name="Lean Bulk",
                meal=["breakfast|eggs", "lunch|rice"],
                notes="high protein",
                activate=True,
                dry_run=False,
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
            )

        self.assertIs(result, expected)
        diet_mock.assert_called_once_with(
            Path("/tmp/brain_ops.sqlite"),
            name="Lean Bulk",
            meals=["breakfast|eggs", "lunch|rice"],
            notes="high protein",
            activate=True,
            dry_run=False,
        )

    def test_create_diet_plan_workflow_publishes_operation_event_when_sink_provided(self) -> None:
        operation = OperationRecord(
            action="create diet plan",
            path=Path("/tmp/brain_ops.sqlite"),
            detail="Diet plan created",
            status=OperationStatus.CREATED,
        )
        expected = SimpleNamespace(operation=operation)
        sink = CollectingEventSink()

        with patch("brain_ops.application.personal.create_diet_plan", return_value=expected):
            result = execute_create_diet_plan_workflow(
                config_path=Path("/tmp/config.yml"),
                name="Lean Bulk",
                meal=["breakfast|eggs"],
                notes=None,
                activate=False,
                dry_run=True,
                load_database_path=lambda _: Path("/tmp/brain_ops.sqlite"),
                event_sink=sink,
            )

        self.assertIs(result, expected)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.personal")
        self.assertEqual(sink.events[0].payload["workflow"], "create-diet-plan")

    def test_capture_workflow_passes_force_type_and_tags(self) -> None:
        expected = SimpleNamespace(path=Path("Inbox/Idea.md"))
        vault = object()

        with patch("brain_ops.application.notes.capture_text", return_value=expected) as capture_mock:
            result = execute_capture_workflow(
                vault,
                text="New idea",
                title="Idea",
                note_type="knowledge_note",
                tags=["x", "y"],
            )

        self.assertIs(result, expected)
        capture_mock.assert_called_once_with(
            vault,
            text="New idea",
            title="Idea",
            force_type="knowledge_note",
            tags=["x", "y"],
        )

    def test_capture_workflow_publishes_operation_event_when_sink_provided(self) -> None:
        operation = OperationRecord(
            action="create note",
            path=Path("Inbox/Idea.md"),
            detail="Captured note",
            status=OperationStatus.CREATED,
        )
        expected = SimpleNamespace(path=Path("Inbox/Idea.md"), operation=operation)
        sink = CollectingEventSink()
        vault = object()

        with patch("brain_ops.application.notes.capture_text", return_value=expected):
            result = execute_capture_workflow(
                vault,
                text="New idea",
                title="Idea",
                note_type="knowledge_note",
                tags=["x", "y"],
                event_sink=sink,
            )

        self.assertIs(result, expected)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.notes")
        self.assertEqual(sink.events[0].payload["workflow"], "capture")
        self.assertEqual(sink.events[0].payload["path"], "Inbox/Idea.md")

    def test_create_note_workflow_builds_request_object(self) -> None:
        expected = SimpleNamespace(path=Path("Knowledge/Test.md"))
        vault = object()

        with patch("brain_ops.application.notes.create_note", return_value=expected) as create_mock:
            result = execute_create_note_workflow(
                vault,
                title="Test",
                note_type="knowledge_note",
                folder="Knowledge",
                template_name="knowledge.md",
                tags=["alpha", "beta"],
                overwrite=True,
            )

        self.assertIs(result, expected)
        self.assertIs(create_mock.call_args.args[0], vault)
        request = create_mock.call_args.args[1]
        self.assertEqual(request.title, "Test")
        self.assertEqual(request.note_type, "knowledge_note")
        self.assertEqual(request.folder, "Knowledge")
        self.assertEqual(request.template_name, "knowledge.md")
        self.assertEqual(request.tags, ["alpha", "beta"])
        self.assertTrue(request.overwrite)

    def test_project_daily_summary_and_improve_workflows_delegate_directly(self) -> None:
        vault = object()
        project_expected = [SimpleNamespace(path=Path("Projects/Test.md"))]
        summary_expected = SimpleNamespace(path=Path("Daily/2026-04-04.md"))
        improve_expected = SimpleNamespace(path=Path("Knowledge/Test.md"))
        note_path = Path("Knowledge/Test.md")

        with (
            patch("brain_ops.application.notes.create_project_scaffold", return_value=project_expected) as project_mock,
            patch("brain_ops.application.notes.write_daily_summary", return_value=summary_expected) as summary_mock,
            patch("brain_ops.application.notes.improve_note", return_value=improve_expected) as improve_mock,
        ):
            project_result = execute_create_project_workflow(vault, name="Test Project")
            summary_result = execute_daily_summary_workflow(vault, date="2026-04-04")
            improve_result = execute_improve_note_workflow(vault, note_path=note_path)

        self.assertIs(project_result, project_expected)
        self.assertIs(summary_result, summary_expected)
        self.assertIs(improve_result, improve_expected)
        project_mock.assert_called_once_with(vault, "Test Project")
        summary_mock.assert_called_once_with(vault, date_text="2026-04-04")
        improve_mock.assert_called_once_with(vault, note_path=note_path)

    def test_project_workflow_publishes_events_for_each_operation(self) -> None:
        vault = object()
        operations = [
            OperationRecord(
                action="create note",
                path=Path("Projects/Test/Overview.md"),
                detail="Overview",
                status=OperationStatus.CREATED,
            ),
            OperationRecord(
                action="create note",
                path=Path("Projects/Test/Tasks.md"),
                detail="Tasks",
                status=OperationStatus.CREATED,
            ),
        ]
        sink = CollectingEventSink()

        with patch("brain_ops.application.notes.create_project_scaffold", return_value=operations):
            result = execute_create_project_workflow(vault, name="Test Project", event_sink=sink)

        self.assertEqual(result, operations)
        self.assertEqual(len(sink.events), 2)
        self.assertEqual({event.payload["workflow"] for event in sink.events}, {"create-project"})
        self.assertEqual(
            {event.payload["path"] for event in sink.events},
            {"Projects/Test/Overview.md", "Projects/Test/Tasks.md"},
        )

    def test_research_note_workflow_preserves_query_and_source_limit(self) -> None:
        expected = SimpleNamespace(reason="researched")
        vault = object()
        note_path = Path("Knowledge/Test.md")

        with patch("brain_ops.application.notes.research_note", return_value=expected) as research_mock:
            result = execute_research_note_workflow(
                vault,
                note_path=note_path,
                query="protein synthesis",
                max_sources=4,
            )

        self.assertIs(result, expected)
        research_mock.assert_called_once_with(
            vault,
            note_path=note_path,
            query="protein synthesis",
            max_sources=4,
        )

    def test_enrich_note_workflow_preserves_flags_and_limits(self) -> None:
        expected = SimpleNamespace(reason="enriched")
        vault = object()
        note_path = Path("Knowledge/Test.md")

        with patch("brain_ops.application.notes.enrich_note", return_value=expected) as enrich_mock:
            result = execute_enrich_note_workflow(
                vault,
                note_path=note_path,
                query="habit formation",
                max_sources=3,
                link_limit=7,
                improve=True,
                research=False,
                apply_links=True,
            )

        self.assertIs(result, expected)
        enrich_mock.assert_called_once_with(
            vault,
            note_path=note_path,
            query="habit formation",
            max_sources=3,
            link_limit=7,
            improve=True,
            research=False,
            apply_links=True,
        )

    def test_link_apply_and_promote_workflows_delegate_expected_arguments(self) -> None:
        vault = object()
        note_path = Path("Knowledge/Test.md")
        suggestions_expected = SimpleNamespace(reason="suggested")
        apply_expected = SimpleNamespace(reason="applied")
        promote_expected = SimpleNamespace(reason="promoted")

        with (
            patch("brain_ops.application.notes.suggest_links", return_value=suggestions_expected) as suggest_mock,
            patch("brain_ops.application.notes.apply_link_suggestions", return_value=apply_expected) as apply_mock,
            patch("brain_ops.application.notes.promote_note", return_value=promote_expected) as promote_mock,
        ):
            suggestions_result = execute_link_suggestions_workflow(vault, note_path=note_path, limit=6)
            apply_result = execute_apply_link_suggestions_workflow(vault, note_path=note_path, limit=3)
            promote_result = execute_promote_note_workflow(vault, note_path=note_path, target_type="knowledge")

        self.assertIs(suggestions_result, suggestions_expected)
        self.assertIs(apply_result, apply_expected)
        self.assertIs(promote_result, promote_expected)
        suggest_mock.assert_called_once_with(vault, note_path=note_path, limit=6)
        apply_mock.assert_called_once_with(vault, note_path=note_path, limit=3)
        promote_mock.assert_called_once_with(vault, note_path=note_path, target_type="knowledge")

    def test_info_workflow_delegates_to_config_loader(self) -> None:
        config = VaultConfig(vault_path=Path("/tmp/vault"))
        loader_calls: list[Path | None] = []

        def load_config(config_path: Path | None):
            loader_calls.append(config_path)
            return config

        result = execute_info_workflow(
            config_path=Path("/tmp/config.yml"),
            load_config=load_config,
        )

        self.assertIs(result, config)
        self.assertEqual(loader_calls, [Path("/tmp/config.yml")])

    def test_init_workflow_builds_vault_config_and_passes_flags(self) -> None:
        expected = [SimpleNamespace(action="write config")]
        captured: dict[str, object] = {}

        def initialize_config(**kwargs):
            captured.update(kwargs)
            return expected

        result = execute_init_workflow(
            vault_path=Path("/tmp/vault"),
            config_output=Path("/tmp/brain-ops.yml"),
            force=True,
            dry_run=True,
            initialize_config=initialize_config,
        )

        self.assertIs(result, expected)
        self.assertIsInstance(captured["config"], VaultConfig)
        self.assertEqual(captured["config"].vault_path, Path("/tmp/vault"))
        self.assertEqual(captured["config_output"], Path("/tmp/brain-ops.yml"))
        self.assertTrue(captured["dry_run"])

    def test_init_workflow_publishes_events_when_operations_are_returned(self) -> None:
        operations = [
            OperationRecord(
                action="write config",
                path=Path("/tmp/brain-ops.yml"),
                detail="Config initialized",
                status=OperationStatus.CREATED,
            )
        ]
        sink = CollectingEventSink()

        result = execute_init_workflow(
            vault_path=Path("/tmp/vault"),
            config_output=Path("/tmp/brain-ops.yml"),
            force=True,
            dry_run=True,
            initialize_config=lambda **_kwargs: operations,
            event_sink=sink,
        )

        self.assertIs(result, operations)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.system")
        self.assertEqual(sink.events[0].payload["workflow"], "init")

    def test_init_workflow_rejects_existing_config_without_force(self) -> None:
        with self.assertRaises(ConfigError):
            execute_init_workflow(
                vault_path=Path("/tmp/vault"),
                config_output=Path(__file__),
                force=False,
                dry_run=True,
                initialize_config=lambda **_kwargs: [],
            )

    def test_init_db_workflow_resolves_database_path_from_loaded_config(self) -> None:
        config = VaultConfig(vault_path=Path("/tmp/vault"), database_path=Path("~/brain-ops.sqlite"))
        expected = [SimpleNamespace(action="init db")]

        with patch(
            "brain_ops.application.system.resolve_database_path",
            return_value=Path("/tmp/db.sqlite"),
        ) as resolve_mock:
            result = execute_init_db_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                load_config=lambda _path: config,
                initialize_database=lambda path, *, dry_run: expected
                if path == Path("/tmp/db.sqlite") and dry_run
                else [],
            )

        self.assertIs(result, expected)
        resolve_mock.assert_called_once_with(config.database_path)

    def test_init_db_workflow_publishes_events_when_operations_are_returned(self) -> None:
        config = VaultConfig(vault_path=Path("/tmp/vault"), database_path=Path("~/brain-ops.sqlite"))
        operations = [
            OperationRecord(
                action="initialize database",
                path=Path("/tmp/db.sqlite"),
                detail="SQLite schema initialized",
                status=OperationStatus.CREATED,
            )
        ]
        sink = CollectingEventSink()

        with patch(
            "brain_ops.application.system.resolve_database_path",
            return_value=Path("/tmp/db.sqlite"),
        ):
            result = execute_init_db_workflow(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                load_config=lambda _path: config,
                initialize_database=lambda path, *, dry_run: operations
                if path == Path("/tmp/db.sqlite") and dry_run
                else [],
                event_sink=sink,
            )

        self.assertIs(result, operations)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].name, "operation.created")
        self.assertEqual(sink.events[0].source, "application.system")
        self.assertEqual(sink.events[0].payload["workflow"], "init-db")

    def test_openclaw_manifest_workflow_writes_only_when_output_present(self) -> None:
        write_calls: list[Path] = []

        def write_manifest(path: Path) -> Path:
            write_calls.append(path)
            return path

        self.assertIsNone(
            execute_openclaw_manifest_workflow(output=None, write_manifest=write_manifest)
        )
        written = execute_openclaw_manifest_workflow(
            output=Path("/tmp/openclaw.json"),
            write_manifest=write_manifest,
        )

        self.assertEqual(written, Path("/tmp/openclaw.json"))
        self.assertEqual(write_calls, [Path("/tmp/openclaw.json")])
