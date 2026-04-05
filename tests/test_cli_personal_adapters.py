from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.interfaces.cli.personal import (
    present_active_diet_command,
    run_spending_summary_command,
)
from brain_ops.interfaces.cli.personal_logging import (
    present_log_expense_command,
    run_log_body_metrics_command,
)
from brain_ops.interfaces.cli.personal_management import (
    present_set_macro_targets_command,
    run_create_diet_plan_command,
)


class CliPersonalAdaptersTestCase(TestCase):
    def test_run_spending_summary_command_delegates_to_application_workflow(self) -> None:
        result = object()

        with patch(
            "brain_ops.interfaces.cli.personal.execute_spending_summary_workflow",
            return_value=result,
        ) as workflow_mock:
            observed = run_spending_summary_command(
                config_path=Path("/tmp/config.yml"),
                date="2026-04-04",
                currency="USD",
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            date="2026-04-04",
            currency="USD",
            load_database_path=workflow_mock.call_args.kwargs["load_database_path"],
        )

    def test_present_active_diet_command_uses_optional_json_renderer(self) -> None:
        console = Mock()
        summary = Mock()

        with (
            patch("brain_ops.interfaces.cli.personal.run_active_diet_command", return_value=summary) as run_mock,
            patch("brain_ops.interfaces.cli.personal.render_active_diet", return_value="active diet") as render_mock,
            patch("brain_ops.interfaces.cli.personal.print_optional_json_or_rendered") as present_mock,
        ):
            present_active_diet_command(
                console,
                config_path=Path("/tmp/config.yml"),
                as_json=True,
            )

        run_mock.assert_called_once_with(config_path=Path("/tmp/config.yml"))
        render_mock.assert_called_once_with(summary)
        present_mock.assert_called_once_with(
            console,
            as_json=True,
            value=summary,
            rendered="active diet",
        )

    def test_run_log_body_metrics_command_delegates_to_application_workflow(self) -> None:
        result = object()
        sink = object()

        with patch(
            "brain_ops.interfaces.cli.personal_logging.execute_log_body_metrics_workflow",
            return_value=result,
        ) as workflow_mock, patch(
            "brain_ops.interfaces.cli.personal_logging.load_event_sink",
            return_value=sink,
        ):
            observed = run_log_body_metrics_command(
                config_path=Path("/tmp/config.yml"),
                weight_kg=80.0,
                body_fat_pct=15.0,
                fat_mass_kg=None,
                muscle_mass_kg=None,
                visceral_fat=None,
                bmr_calories=None,
                arm_cm=None,
                waist_cm=None,
                thigh_cm=None,
                calf_cm=None,
                logged_at="2026-04-04T08:00:00",
                note="check-in",
                dry_run=True,
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            weight_kg=80.0,
            body_fat_pct=15.0,
            fat_mass_kg=None,
            muscle_mass_kg=None,
            visceral_fat=None,
            bmr_calories=None,
            arm_cm=None,
            waist_cm=None,
            thigh_cm=None,
            calf_cm=None,
            note="check-in",
            logged_at="2026-04-04T08:00:00",
            dry_run=True,
            load_database_path=workflow_mock.call_args.kwargs["load_database_path"],
            event_sink=sink,
        )

    def test_present_log_expense_command_renders_operations_result(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.personal_logging.run_log_expense_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.personal_logging.render_expense_log", return_value="expense log") as render_mock,
            patch("brain_ops.interfaces.cli.personal_logging.print_rendered_with_operations") as present_mock,
        ):
            present_log_expense_command(
                console,
                config_path=Path("/tmp/config.yml"),
                amount=25.5,
                category="food",
                merchant="Store",
                currency="USD",
                note="snack",
                dry_run=False,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            amount=25.5,
            category="food",
            merchant="Store",
            currency="USD",
            note="snack",
            dry_run=False,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(console, result.operations, "expense log")

    def test_run_create_diet_plan_command_delegates_to_application_workflow(self) -> None:
        result = object()
        sink = object()

        with patch(
            "brain_ops.interfaces.cli.personal_management.execute_create_diet_plan_workflow",
            return_value=result,
        ) as workflow_mock, patch(
            "brain_ops.interfaces.cli.personal_management.load_event_sink",
            return_value=sink,
        ):
            observed = run_create_diet_plan_command(
                config_path=Path("/tmp/config.yml"),
                name="Lean Bulk",
                meal=["breakfast|eggs"],
                notes="high protein",
                activate=True,
                dry_run=False,
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            name="Lean Bulk",
            meal=["breakfast|eggs"],
            notes="high protein",
            activate=True,
            dry_run=False,
            load_database_path=workflow_mock.call_args.kwargs["load_database_path"],
            event_sink=sink,
        )

    def test_present_set_macro_targets_command_renders_operations_result(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object(), object()]

        with (
            patch("brain_ops.interfaces.cli.personal_management.run_set_macro_targets_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.personal_management.render_macro_targets", return_value="macro targets") as render_mock,
            patch("brain_ops.interfaces.cli.personal_management.print_rendered_with_operations") as present_mock,
        ):
            present_set_macro_targets_command(
                console,
                config_path=Path("/tmp/config.yml"),
                calories=2500,
                protein_g=180,
                carbs_g=250,
                fat_g=70,
                dry_run=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            calories=2500,
            protein_g=180,
            carbs_g=250,
            fat_g=70,
            dry_run=True,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(console, result.operations, "macro targets")
