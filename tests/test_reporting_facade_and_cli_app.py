from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from brain_ops import reporting
from brain_ops.interfaces.cli.app import create_cli_app


class ReportingFacadeAndCliAppTestCase(TestCase):
    def test_reporting_facade_reexports_specialized_renderers(self) -> None:
        from brain_ops import reporting_conversation, reporting_knowledge, reporting_personal

        self.assertIs(reporting.render_route_decision, reporting_conversation.render_route_decision)
        self.assertIs(reporting.render_handle_input, reporting_conversation.render_handle_input)
        self.assertIs(reporting.render_inbox_report, reporting_knowledge.render_inbox_report)
        self.assertIs(reporting.render_weekly_review, reporting_knowledge.render_weekly_review)
        self.assertIs(reporting.render_daily_summary, reporting_knowledge.render_daily_summary)
        self.assertIs(reporting.render_daily_macros, reporting_personal.render_daily_macros)
        self.assertIs(reporting.render_active_diet, reporting_personal.render_active_diet)
        self.assertIs(reporting.render_workout_status, reporting_personal.render_workout_status)

    def test_reporting_facade_all_exports_are_present(self) -> None:
        exported = set(reporting.__all__)

        self.assertIn("render_route_decision", exported)
        self.assertIn("render_handle_input", exported)
        self.assertIn("render_inbox_report", exported)
        self.assertIn("render_weekly_review", exported)
        self.assertIn("render_daily_macros", exported)
        self.assertIn("render_active_diet", exported)
        self.assertIn("render_workout_status", exported)

    def test_create_cli_app_builds_app_and_registers_commands_with_error_handler(self) -> None:
        with patch("brain_ops.interfaces.cli.app.register_cli_commands") as register_mock:
            app = create_cli_app(version="1.2.3")

        self.assertIsNotNone(app)
        register_mock.assert_called_once()
        called_app, called_console, called_handler = register_mock.call_args.args[:3]
        self.assertIs(called_app, app)
        self.assertIsNotNone(called_console)
        self.assertTrue(callable(called_handler))
        self.assertEqual(register_mock.call_args.kwargs["version"], "1.2.3")

    def test_create_cli_app_error_handler_routes_brain_ops_errors(self) -> None:
        captured_handler = None

        def capture_register(_app, _console, handle_error, **_kwargs):
            nonlocal captured_handler
            captured_handler = handle_error

        with (
            patch("brain_ops.interfaces.cli.app.register_cli_commands", side_effect=capture_register),
            patch("brain_ops.interfaces.cli.app.exit_with_brain_ops_error") as exit_mock,
        ):
            app = create_cli_app(version="1.2.3")
            self.assertIsNotNone(app)
            error = Exception("boom")
            # The handler is typed for BrainOpsError, but it only forwards the object.
            captured_handler(error)

        exit_mock.assert_called_once()
        forwarded_console, forwarded_error = exit_mock.call_args.args
        self.assertIsNotNone(forwarded_console)
        self.assertIs(forwarded_error, error)


if __name__ == "__main__":
    import unittest

    unittest.main()
