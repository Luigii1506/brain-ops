from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.application.alerts import AlertMessage
from brain_ops.errors import ConfigError
from brain_ops.application.automation import (
    ALERT_DELIVERY_PRESETS,
    AlertDelivery,
    AlertDeliveryPolicy,
    AlertDeliveryPreset,
    build_alert_delivery_policy,
    deliver_alert_via_target,
    execute_alert_delivery_presets_workflow,
    execute_event_log_alert_delivery_workflow,
    render_alert_message_text,
    resolve_alert_delivery_latest_path,
    resolve_alert_delivery_output_path,
    resolve_alert_delivery_target_paths,
)


class ApplicationAutomationTestCase(TestCase):
    def test_render_alert_message_text_renders_key_fields(self) -> None:
        message = AlertMessage(
            level="alert",
            title="Event log alert check triggered 1 rule(s)",
            summary="summary text",
            triggered_rules=["total_events>1 (3)"],
            highlights={"latest_day": "2026-04-04", "total_events": 3},
        )

        rendered = render_alert_message_text(message)

        self.assertIn("level: alert", rendered)
        self.assertIn("title: Event log alert check triggered 1 rule(s)", rendered)
        self.assertIn("triggered_rules: total_events>1 (3)", rendered)
        self.assertIn("latest_day: 2026-04-04", rendered)

    def test_build_delivery_policy_and_resolve_output_path_use_source_workflow_and_level(self) -> None:
        policy = build_alert_delivery_policy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
        )
        message = AlertMessage(
            level="alert",
            title="title",
            summary="summary",
            triggered_rules=[],
            highlights={},
        )

        path = resolve_alert_delivery_output_path(
            policy,
            message=message,
            source="application.notes",
            workflow="capture",
        )
        latest_path = resolve_alert_delivery_latest_path(policy)

        self.assertEqual(
            policy,
            AlertDeliveryPolicy(
                output_dir=Path("/tmp/alerts"),
                output_format="json",
                filename_prefix="event-log-alert",
                write_latest=True,
                delivery_mode="both",
                target="file",
            ),
        )
        self.assertEqual(
            path,
            Path("/tmp/alerts/event-log-alert-application-notes-capture-alert.json"),
        )
        self.assertEqual(latest_path, Path("/tmp/alerts/event-log-alert-latest.json"))

    def test_execute_event_log_alert_delivery_workflow_writes_json_output(self) -> None:
        message = AlertMessage(
            level="ok",
            title="Event log alert check passed",
            summary="summary text",
            triggered_rules=[],
            highlights={"latest_day": "2026-04-04", "total_events": 0},
        )
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "alerts" / "event-log-alert.json"

            delivery = execute_event_log_alert_delivery_workflow(
                event_log_path=Path("~/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="default",
                max_total_events=None,
                max_latest_day_events=None,
                output_path=output_path,
                output_format="json",
                delivery_mode="both",
                target="file",
                resolve_output_dir=lambda explicit_path, **_: explicit_path.parent,
                load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
                execute_alert_message=lambda **kwargs: message,
            )

            self.assertEqual(
                delivery,
                AlertDelivery(
                    message=message,
                    output_path=output_path,
                    output_format="json",
                    target="file",
                    latest_path=output_path.parent / "event-log-alert-latest.json",
                ),
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, message.to_dict())
            latest_payload = json.loads((output_path.parent / "event-log-alert-latest.json").read_text(encoding="utf-8"))
            self.assertEqual(latest_payload, message.to_dict())

    def test_execute_event_log_alert_delivery_workflow_can_derive_output_path_from_policy(self) -> None:
        message = AlertMessage(
            level="ok",
            title="Event log alert check passed",
            summary="summary text",
            triggered_rules=[],
            highlights={"latest_day": "2026-04-04", "total_events": 0},
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "alerts"

            delivery = execute_event_log_alert_delivery_workflow(
                event_log_path=Path("~/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="default",
                max_total_events=None,
                max_latest_day_events=None,
                output_path=None,
                output_format="text",
                delivery_mode="both",
                target="file",
                resolve_output_dir=lambda _explicit_path, **_: output_dir,
                load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
                execute_alert_message=lambda **kwargs: message,
            )

            self.assertEqual(
                delivery.output_path,
                output_dir / "event-log-alert-application-notes-capture-ok.txt",
            )
            self.assertEqual(
                delivery.latest_path,
                output_dir / "event-log-alert-latest.txt",
            )
            self.assertTrue(delivery.output_path.exists())
            self.assertTrue(delivery.latest_path.exists())
            self.assertIn("level: ok", delivery.output_path.read_text(encoding="utf-8"))

    def test_execute_event_log_alert_delivery_workflow_rejects_unknown_format(self) -> None:
        message = AlertMessage(
            level="ok",
            title="title",
            summary="summary",
            triggered_rules=[],
            highlights={},
        )
        with self.assertRaises(ValueError):
            execute_event_log_alert_delivery_workflow(
                event_log_path=None,
                top=3,
                limit=2,
                source=None,
                workflow=None,
                since=None,
                until=None,
                preset=None,
                max_total_events=None,
                max_latest_day_events=None,
                output_path=Path("/tmp/alert.out"),
                output_format="xml",
                delivery_mode="both",
                target="file",
                resolve_output_dir=lambda explicit_path, **_: explicit_path.parent,
                load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
                execute_alert_message=lambda **kwargs: message,
            )

    def test_resolve_alert_delivery_target_paths_support_archive_latest_and_both(self) -> None:
        message = AlertMessage(
            level="alert",
            title="title",
            summary="summary",
            triggered_rules=[],
            highlights={},
        )
        both_policy = AlertDeliveryPolicy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
            filename_prefix="event-log-alert",
            write_latest=True,
            delivery_mode="both",
            target="file",
        )
        archive_policy = AlertDeliveryPolicy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
            filename_prefix="event-log-alert",
            write_latest=True,
            delivery_mode="archive",
            target="file",
        )
        latest_policy = AlertDeliveryPolicy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
            filename_prefix="event-log-alert",
            write_latest=True,
            delivery_mode="latest",
            target="file",
        )

        self.assertEqual(
            resolve_alert_delivery_target_paths(
                both_policy,
                message=message,
                source="application.notes",
                workflow="capture",
                explicit_output_path=None,
            ),
            (
                Path("/tmp/alerts/event-log-alert-application-notes-capture-alert.json"),
                Path("/tmp/alerts/event-log-alert-latest.json"),
            ),
        )
        self.assertEqual(
            resolve_alert_delivery_target_paths(
                archive_policy,
                message=message,
                source="application.notes",
                workflow="capture",
                explicit_output_path=None,
            ),
            (
                Path("/tmp/alerts/event-log-alert-application-notes-capture-alert.json"),
                None,
            ),
        )
        self.assertEqual(
            resolve_alert_delivery_target_paths(
                latest_policy,
                message=message,
                source="application.notes",
                workflow="capture",
                explicit_output_path=None,
            ),
            (
                Path("/tmp/alerts/event-log-alert-latest.json"),
                None,
            ),
        )

    def test_deliver_alert_via_target_writes_file_outputs(self) -> None:
        policy = AlertDeliveryPolicy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
            filename_prefix="event-log-alert",
            write_latest=True,
            delivery_mode="both",
            target="file",
        )
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "alert.json"
            latest_path = Path(temp_dir) / "latest.json"

            written_path, delivered_latest_path = deliver_alert_via_target(
                policy,
                payload='{"ok": true}\n',
                output_path=output_path,
                latest_path=latest_path,
            )

            self.assertEqual(written_path, output_path)
            self.assertEqual(delivered_latest_path, latest_path)
            self.assertEqual(output_path.read_text(encoding="utf-8"), '{"ok": true}\n')
            self.assertEqual(latest_path.read_text(encoding="utf-8"), '{"ok": true}\n')

    def test_deliver_alert_via_target_supports_stdout_without_writing_files(self) -> None:
        policy = AlertDeliveryPolicy(
            output_dir=Path("/tmp/alerts"),
            output_format="json",
            filename_prefix="event-log-alert",
            write_latest=True,
            delivery_mode="both",
            target="stdout",
        )

        written_path, delivered_latest_path = deliver_alert_via_target(
            policy,
            payload='{"ok": true}\n',
            output_path=Path("/tmp/alerts/ignored.json"),
            latest_path=Path("/tmp/alerts/latest.json"),
        )

        self.assertEqual(written_path, Path("<stdout>"))
        self.assertIsNone(delivered_latest_path)

    def test_execute_event_log_alert_delivery_workflow_supports_stdout_target(self) -> None:
        message = AlertMessage(
            level="alert",
            title="Event log alert check triggered 1 rule(s)",
            summary="summary text",
            triggered_rules=["total_events>1 (3)"],
            highlights={"latest_day": "2026-04-04", "total_events": 3},
        )

        delivery = execute_event_log_alert_delivery_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=3,
            limit=2,
            source="application.notes",
            workflow="capture",
            since="2026-04-04",
            until="2026-04-05",
            preset="default",
            max_total_events=None,
            max_latest_day_events=None,
            output_path=None,
            output_format="text",
            delivery_mode="both",
            target="stdout",
            resolve_output_dir=lambda _explicit_path, **_: Path("/tmp/alerts"),
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            execute_alert_message=lambda **kwargs: message,
        )

        self.assertEqual(delivery.output_path, Path("<stdout>"))
        self.assertEqual(delivery.target, "stdout")
        self.assertIsNone(delivery.latest_path)

    def test_alert_delivery_presets_contain_expected_named_entries(self) -> None:
        self.assertIn("default", ALERT_DELIVERY_PRESETS)
        self.assertIn("file-text", ALERT_DELIVERY_PRESETS)
        self.assertIn("stdout-json", ALERT_DELIVERY_PRESETS)
        self.assertIn("stdout-text", ALERT_DELIVERY_PRESETS)
        self.assertIn("archive-only", ALERT_DELIVERY_PRESETS)

        default = ALERT_DELIVERY_PRESETS["default"]
        self.assertEqual(default.output_format, "json")
        self.assertEqual(default.target, "file")
        self.assertEqual(default.delivery_mode, "both")

        stdout_text = ALERT_DELIVERY_PRESETS["stdout-text"]
        self.assertEqual(stdout_text.output_format, "text")
        self.assertEqual(stdout_text.target, "stdout")
        self.assertEqual(stdout_text.delivery_mode, "archive")

    def test_execute_alert_delivery_presets_workflow_returns_copy(self) -> None:
        result = execute_alert_delivery_presets_workflow()
        self.assertEqual(set(result.keys()), set(ALERT_DELIVERY_PRESETS.keys()))
        self.assertIsNot(result, ALERT_DELIVERY_PRESETS)

    def test_alert_delivery_preset_to_dict_includes_all_fields(self) -> None:
        preset = AlertDeliveryPreset(output_format="text", target="stdout", delivery_mode="archive")
        d = preset.to_dict()
        self.assertEqual(d["output_format"], "text")
        self.assertEqual(d["target"], "stdout")
        self.assertEqual(d["delivery_mode"], "archive")
        self.assertIn("filename_prefix", d)
        self.assertIn("write_latest", d)

    def test_build_alert_delivery_policy_uses_preset_defaults(self) -> None:
        policy = build_alert_delivery_policy(
            output_dir=Path("/tmp/alerts"),
            preset="stdout-json",
        )
        self.assertEqual(policy.output_format, "json")
        self.assertEqual(policy.target, "stdout")
        self.assertEqual(policy.delivery_mode, "archive")

    def test_build_alert_delivery_policy_explicit_args_override_preset(self) -> None:
        policy = build_alert_delivery_policy(
            output_dir=Path("/tmp/alerts"),
            preset="stdout-json",
            output_format="text",
        )
        self.assertEqual(policy.output_format, "text")
        self.assertEqual(policy.target, "stdout")

    def test_build_alert_delivery_policy_rejects_unknown_preset(self) -> None:
        with self.assertRaises(ConfigError):
            build_alert_delivery_policy(
                output_dir=Path("/tmp/alerts"),
                preset="nonexistent",
            )

    def test_build_alert_delivery_policy_defaults_to_default_preset_when_no_preset_given(self) -> None:
        policy = build_alert_delivery_policy(
            output_dir=Path("/tmp/alerts"),
        )
        self.assertEqual(policy.output_format, "json")
        self.assertEqual(policy.target, "file")
        self.assertEqual(policy.delivery_mode, "both")

    def test_execute_event_log_alert_delivery_workflow_supports_delivery_preset(self) -> None:
        message = AlertMessage(
            level="ok",
            title="Event log alert check passed",
            summary="summary text",
            triggered_rules=[],
            highlights={"latest_day": "2026-04-04", "total_events": 0},
        )

        delivery = execute_event_log_alert_delivery_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=3,
            limit=2,
            source=None,
            workflow=None,
            since=None,
            until=None,
            preset=None,
            max_total_events=None,
            max_latest_day_events=None,
            output_path=None,
            output_format=None,
            delivery_mode=None,
            target=None,
            delivery_preset="stdout-text",
            resolve_output_dir=lambda _explicit_path, **_: Path("/tmp/alerts"),
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            execute_alert_message=lambda **kwargs: message,
        )

        self.assertEqual(delivery.target, "stdout")
        self.assertEqual(delivery.output_format, "text")
        self.assertEqual(delivery.output_path, Path("<stdout>"))
