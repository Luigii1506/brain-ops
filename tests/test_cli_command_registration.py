from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

import typer
from rich.console import Console
from typer.testing import CliRunner

from brain_ops.errors import BrainOpsError
from brain_ops.interfaces.cli.app import create_cli_app
from brain_ops.interfaces.cli.commands import register_cli_commands
from brain_ops.interfaces.cli.commands_core import register_core_commands
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands
from brain_ops.interfaces.cli.commands_personal import register_personal_commands
from brain_ops.interfaces.cli.commands_projects import register_project_commands
from brain_ops.interfaces.cli.commands_scheduling import register_scheduling_commands
from brain_ops.interfaces.cli.commands_sources import register_source_commands


class CliCommandRegistrationTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()

    @staticmethod
    def _command_names(app: typer.Typer) -> set[str]:
        return {
            command.name if command.name is not None else command.callback.__name__
            for command in app.registered_commands
        }

    def test_register_core_commands_registers_expected_names(self) -> None:
        app = typer.Typer()

        register_core_commands(
            app,
            self.console,
            self.handle_error,
            version="1.0.0",
            print_operations=Mock(),
        )

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "info",
                "openclaw-manifest",
                "init",
                "init-db",
                "event-log-summary",
                "event-log-tail",
                "event-log-report",
                "event-log-hotspots",
                "event-log-failures",
                "event-log-alerts",
                "event-log-alert-check",
                "event-log-alert-message",
                "event-log-alert-deliver",
                "event-log-alert-delivery-presets",
                "event-log-alert-presets",
                "daily-summary",
                "route-input",
                "handle-input",
            },
        )

    def test_register_personal_commands_registers_expected_names(self) -> None:
        app = typer.Typer()
        register_personal_commands(app, self.console, self.handle_error)

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "log-meal",
                "daily-macros",
                "set-macro-targets",
                "macro-status",
                "create-diet-plan",
                "set-active-diet",
                "active-diet",
                "diet-status",
                "update-diet-meal",
                "log-supplement",
                "habit-checkin",
                "daily-habits",
                "set-habit-target",
                "habit-status",
                "log-body-metrics",
                "body-metrics-status",
                "log-workout",
                "workout-status",
                "log-expense",
                "spending-summary",
                "set-budget-target",
                "budget-status",
                "daily-log",
                "daily-status",
                "daily-review",
                "week-review",
                "capture",
            },
        )

    def test_register_note_and_knowledge_commands_registers_expected_names(self) -> None:
        app = typer.Typer()
        register_note_and_knowledge_commands(app, self.console, self.handle_error)

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "create-entity",
                "create-note",
                "create-project",
                "check-coverage",
                "compile-knowledge",
                "entity-index",
                "full-enrich",
                "enrich-entity",
                "audit-knowledge",
                "entity-relations",
                "generate-moc",
                "suggest-entities",
                "ingest-source",
                "list-extractions",
                "multi-enrich",
                "plan-direct-enrich",
                "post-process",
                "query-knowledge",
                "reconcile",
                "registry-lint",
                "search-knowledge",
                "process-inbox",
                "weekly-review",
                "audit-vault",
                "normalize-frontmatter",
                "capture-note",
                "improve-note",
                "research-note",
                "link-suggestions",
                "apply-link-suggestions",
                "promote-note",
                "enrich-note",
            },
        )

    def test_register_project_commands_registers_expected_names(self) -> None:
        app = typer.Typer()
        register_project_commands(app, self.console, self.handle_error)

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "register-project",
                "list-projects",
                "project-context",
                "update-project-context",
                "generate-claude-md",
                "generate-all-claude-md",
                "session",
                "project-log",
                "audit-project",
                "refresh-project",
            },
        )

    def test_register_source_commands_registers_expected_names(self) -> None:
        app = typer.Typer()
        register_source_commands(app, self.console, self.handle_error)

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "add-source",
                "list-sources",
                "remove-source",
                "check-source",
                "check-all-sources",
            },
        )

    def test_register_scheduling_commands_registers_expected_names(self) -> None:
        app = typer.Typer()
        register_scheduling_commands(app, self.console, self.handle_error)

        names = self._command_names(app)
        self.assertEqual(
            names,
            {
                "list-jobs",
                "init-jobs",
                "show-crontab",
            },
        )

    def test_create_cli_app_registers_all_major_command_clusters(self) -> None:
        app = create_cli_app(version="1.0.0", console=self.console)
        names = self._command_names(app)

        self.assertIn("info", names)
        self.assertIn("event-log-summary", names)
        self.assertIn("event-log-tail", names)
        self.assertIn("event-log-report", names)
        self.assertIn("event-log-hotspots", names)
        self.assertIn("event-log-failures", names)
        self.assertIn("event-log-alerts", names)
        self.assertIn("event-log-alert-check", names)
        self.assertIn("route-input", names)
        self.assertIn("daily-macros", names)
        self.assertIn("capture", names)
        self.assertIn("process-inbox", names)
        self.assertIn("enrich-note", names)
        self.assertIn("register-project", names)
        self.assertIn("list-projects", names)
        self.assertIn("project-context", names)
        self.assertIn("generate-claude-md", names)
        self.assertIn("add-source", names)
        self.assertIn("check-source", names)
        self.assertIn("check-all-sources", names)
        self.assertIn("list-jobs", names)
        self.assertIn("init-jobs", names)
        self.assertIn("show-crontab", names)

    def test_register_cli_commands_registers_representative_commands(self) -> None:
        app = typer.Typer()
        register_cli_commands(app, self.console, self.handle_error, version="1.0.0")

        names = self._command_names(app)
        self.assertIn("info", names)
        self.assertIn("event-log-summary", names)
        self.assertIn("event-log-tail", names)
        self.assertIn("event-log-report", names)
        self.assertIn("event-log-hotspots", names)
        self.assertIn("event-log-failures", names)
        self.assertIn("event-log-alerts", names)
        self.assertIn("event-log-alert-check", names)
        self.assertIn("route-input", names)
        self.assertIn("daily-macros", names)
        self.assertIn("process-inbox", names)
        self.assertIn("capture", names)

    def test_route_input_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_route_input_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(app, ["route-input", "hola", "--json"])

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "config_path": None,
                "text": "hola",
                "as_json": True,
                "use_llm": None,
            },
        )

    def test_event_log_summary_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_summary_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-summary",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--status",
                    "created",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "source": "application.notes",
                "workflow": "capture",
                "status": "created",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "as_json": True,
            },
        )

    def test_event_log_tail_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_tail_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-tail",
                    "--path",
                    "/tmp/events.jsonl",
                    "--limit",
                    "4",
                    "--source",
                    "application.personal",
                    "--workflow",
                    "log-expense",
                    "--status",
                    "updated",
                    "--since",
                    "2026-04-04T10:00:00+00:00",
                    "--until",
                    "2026-04-04T12:00:00+00:00",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "limit": 4,
                "source": "application.personal",
                "workflow": "log-expense",
                "status": "updated",
                "since": "2026-04-04T10:00:00+00:00",
                "until": "2026-04-04T12:00:00+00:00",
                "as_json": True,
            },
        )

    def test_event_log_report_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_report_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-report",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--status",
                    "created",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "status": "created",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "as_json": True,
            },
        )

    def test_event_log_hotspots_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_hotspots_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-hotspots",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--status",
                    "created",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "source": "application.notes",
                "workflow": "capture",
                "status": "created",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "as_json": True,
            },
        )

    def test_event_log_failures_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_failures_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-failures",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "as_json": True,
            },
        )

    def test_event_log_alerts_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_alerts_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-alerts",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "as_json": True,
            },
        )

    def test_event_log_alert_check_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_alert_check_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-alert-check",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--preset",
                    "strict",
                    "--max-total-events",
                    "0",
                    "--max-latest-day-events",
                    "1",
                    "--fail-on-alerts",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "preset": "strict",
                "max_total_events": 0,
                "max_latest_day_events": 1,
                "fail_on_alerts": True,
                "as_json": True,
            },
        )

    def test_event_log_alert_presets_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_alert_presets_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(app, ["event-log-alert-presets", "--json"])

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "as_json": True,
            },
        )

    def test_event_log_alert_message_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_alert_message_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-alert-message",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--preset",
                    "strict",
                    "--max-total-events",
                    "0",
                    "--max-latest-day-events",
                    "1",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "preset": "strict",
                "max_total_events": 0,
                "max_latest_day_events": 1,
                "as_json": True,
            },
        )

    def test_event_log_alert_delivery_presets_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_alert_delivery_presets_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(app, ["event-log-alert-delivery-presets", "--json"])

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "as_json": True,
            },
        )

    def test_event_log_alert_deliver_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_core.present_event_log_alert_delivery_command") as presenter_mock:
            register_core_commands(
                app,
                self.console,
                self.handle_error,
                version="1.0.0",
                print_operations=Mock(),
            )
            result = self.runner.invoke(
                app,
                [
                    "event-log-alert-deliver",
                    "--format",
                    "json",
                    "--delivery-mode",
                    "latest",
                    "--target",
                    "file",
                    "--delivery-preset",
                    "default",
                    "--path",
                    "/tmp/events.jsonl",
                    "--top",
                    "3",
                    "--limit",
                    "2",
                    "--source",
                    "application.notes",
                    "--workflow",
                    "capture",
                    "--since",
                    "2026-04-04",
                    "--until",
                    "2026-04-05",
                    "--preset",
                    "strict",
                    "--max-total-events",
                    "0",
                    "--max-latest-day-events",
                    "1",
                    "--json",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "preset": "strict",
                "max_total_events": 0,
                "max_latest_day_events": 1,
                "output_path": None,
                "output_format": "json",
                "delivery_mode": "latest",
                "target": "file",
                "delivery_preset": "default",
                "as_json": True,
            },
        )

    def test_daily_macros_command_delegates_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_personal.present_daily_macros_command") as presenter_mock:
            register_personal_commands(app, self.console, self.handle_error)
            result = self.runner.invoke(app, ["daily-macros", "--date", "2026-04-04", "--json"])

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "config_path": None,
                "date": "2026-04-04",
                "as_json": True,
            },
        )

    def test_capture_note_command_routes_brain_ops_error_to_handler(self) -> None:
        app = typer.Typer()
        error = BrainOpsError("boom")

        with patch(
            "brain_ops.interfaces.cli.commands_notes.present_capture_command",
            side_effect=error,
        ):
            register_note_and_knowledge_commands(app, self.console, self.handle_error)
            result = self.runner.invoke(app, ["capture-note", "texto libre"])

        self.assertEqual(result.exit_code, 0)
        self.handle_error.assert_called_once_with(error)

    def test_process_inbox_command_delegates_flags_to_presenter(self) -> None:
        app = typer.Typer()
        with patch("brain_ops.interfaces.cli.commands_notes.present_process_inbox_command") as presenter_mock:
            register_note_and_knowledge_commands(app, self.console, self.handle_error)
            result = self.runner.invoke(
                app,
                [
                    "process-inbox",
                    "--dry-run",
                    "--write-report",
                    "--no-improve-structure",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        presenter_mock.assert_called_once()
        self.assertEqual(
            presenter_mock.call_args.kwargs,
            {
                "config_path": None,
                "dry_run": True,
                "write_report": True,
                "improve_structure": False,
            },
        )
