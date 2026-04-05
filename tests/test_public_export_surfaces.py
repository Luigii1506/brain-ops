from __future__ import annotations

from unittest import TestCase

from brain_ops import application
from brain_ops.interfaces import cli, conversation
from brain_ops.storage import obsidian, sqlite


class PublicExportSurfacesTestCase(TestCase):
    def test_application_exports_reuse_workflow_modules(self) -> None:
        from brain_ops.application import alerts as app_alerts
        from brain_ops.application import automation as app_automation
        from brain_ops.application import events as app_events
        from brain_ops.application import conversation as app_conversation
        from brain_ops.application import knowledge as app_knowledge
        from brain_ops.application import monitoring as app_monitoring
        from brain_ops.application import notes as app_notes
        from brain_ops.application import personal as app_personal
        from brain_ops.application import system as app_system

        exported = set(application.__all__)

        self.assertIs(application.AlertDelivery, app_automation.AlertDelivery)
        self.assertIs(application.AlertDeliveryPreset, app_automation.AlertDeliveryPreset)
        self.assertIs(application.ALERT_DELIVERY_PRESETS, app_automation.ALERT_DELIVERY_PRESETS)
        self.assertIs(application.execute_alert_delivery_presets_workflow, app_automation.execute_alert_delivery_presets_workflow)
        self.assertIs(application.AlertMessage, app_alerts.AlertMessage)
        self.assertIs(application.build_event_log_alert_message, app_alerts.build_event_log_alert_message)
        self.assertIs(application.execute_event_log_alert_delivery_workflow, app_automation.execute_event_log_alert_delivery_workflow)
        self.assertIs(application.execute_route_input_workflow, app_conversation.execute_route_input_workflow)
        self.assertIs(application.EVENT_LOG_ALERT_POLICY_PRESETS, app_monitoring.EVENT_LOG_ALERT_POLICY_PRESETS)
        self.assertIs(application.execute_event_log_alert_message_workflow, app_alerts.execute_event_log_alert_message_workflow)
        self.assertIs(application.execute_event_log_alert_presets_workflow, app_monitoring.execute_event_log_alert_presets_workflow)
        self.assertIs(application.execute_event_log_alert_check_workflow, app_monitoring.execute_event_log_alert_check_workflow)
        self.assertIs(application.execute_event_log_alerts_workflow, app_monitoring.execute_event_log_alerts_workflow)
        self.assertIs(application.build_event_log_alert_policy, app_monitoring.build_event_log_alert_policy)
        self.assertIs(application.execute_event_log_failures_workflow, app_monitoring.execute_event_log_failures_workflow)
        self.assertIs(application.execute_event_log_hotspots_workflow, app_monitoring.execute_event_log_hotspots_workflow)
        self.assertIs(application.execute_event_log_report_workflow, app_monitoring.execute_event_log_report_workflow)
        self.assertIs(application.execute_event_log_tail_workflow, app_monitoring.execute_event_log_tail_workflow)
        self.assertIs(application.execute_event_log_summary_workflow, app_monitoring.execute_event_log_summary_workflow)
        self.assertIs(application.execute_create_entity_workflow, app_notes.execute_create_entity_workflow)
        self.assertIs(application.execute_capture_workflow, app_notes.execute_capture_workflow)
        self.assertIs(application.execute_entity_index_workflow, app_knowledge.execute_entity_index_workflow)
        self.assertIs(application.execute_entity_relations_workflow, app_knowledge.execute_entity_relations_workflow)
        self.assertIs(application.execute_process_inbox_workflow, app_knowledge.execute_process_inbox_workflow)
        self.assertIs(application.execute_daily_status_workflow, app_personal.execute_daily_status_workflow)
        self.assertIs(application.execute_openclaw_manifest_workflow, app_system.execute_openclaw_manifest_workflow)
        self.assertIs(application.publish_result_events, app_events.publish_result_events)
        self.assertIs(application.result_operations, app_events.result_operations)

        self.assertIn("AlertDelivery", exported)
        self.assertIn("AlertDeliveryPreset", exported)
        self.assertIn("ALERT_DELIVERY_PRESETS", exported)
        self.assertIn("execute_alert_delivery_presets_workflow", exported)
        self.assertIn("AlertMessage", exported)
        self.assertIn("build_event_log_alert_message", exported)
        self.assertIn("execute_event_log_alert_delivery_workflow", exported)
        self.assertIn("execute_route_input_workflow", exported)
        self.assertIn("EVENT_LOG_ALERT_POLICY_PRESETS", exported)
        self.assertIn("execute_event_log_alert_message_workflow", exported)
        self.assertIn("execute_event_log_alert_presets_workflow", exported)
        self.assertIn("execute_event_log_alert_check_workflow", exported)
        self.assertIn("execute_event_log_alerts_workflow", exported)
        self.assertIn("build_event_log_alert_policy", exported)
        self.assertIn("execute_event_log_failures_workflow", exported)
        self.assertIn("execute_event_log_hotspots_workflow", exported)
        self.assertIn("execute_event_log_report_workflow", exported)
        self.assertIn("execute_event_log_tail_workflow", exported)
        self.assertIn("execute_event_log_summary_workflow", exported)
        self.assertIn("execute_create_entity_workflow", exported)
        self.assertIn("execute_capture_workflow", exported)
        self.assertIn("execute_entity_index_workflow", exported)
        self.assertIn("execute_entity_relations_workflow", exported)
        self.assertIn("execute_process_inbox_workflow", exported)
        self.assertIn("execute_daily_status_workflow", exported)
        self.assertIn("execute_openclaw_manifest_workflow", exported)
        self.assertIn("publish_result_events", exported)
        self.assertIn("result_operations", exported)

    def test_cli_exports_reuse_specialized_adapter_modules(self) -> None:
        from brain_ops.interfaces.cli import automation as cli_automation
        from brain_ops.interfaces.cli import app as cli_app
        from brain_ops.interfaces.cli import commands as cli_commands
        from brain_ops.interfaces.cli import conversation as cli_conversation
        from brain_ops.interfaces.cli import knowledge as cli_knowledge
        from brain_ops.interfaces.cli import monitoring as cli_monitoring
        from brain_ops.interfaces.cli import notes as cli_notes
        from brain_ops.interfaces.cli import personal as cli_personal
        from brain_ops.interfaces.cli import runtime as cli_runtime
        from brain_ops.interfaces.cli import system as cli_system

        exported = set(cli.__all__)

        self.assertIs(cli.create_cli_app, cli_app.create_cli_app)
        self.assertIs(cli.present_alert_delivery_presets_command, cli_automation.present_alert_delivery_presets_command)
        self.assertIs(cli.build_alert_delivery_presets_table, cli_automation.build_alert_delivery_presets_table)
        self.assertIs(cli.present_event_log_alert_delivery_command, cli_automation.present_event_log_alert_delivery_command)
        self.assertIs(cli.register_cli_commands, cli_commands.register_cli_commands)
        self.assertIs(cli.run_route_input_command, cli_conversation.run_route_input_command)
        self.assertIs(cli.present_event_log_alert_message_command, cli_monitoring.present_event_log_alert_message_command)
        self.assertIs(cli.present_event_log_alert_presets_command, cli_monitoring.present_event_log_alert_presets_command)
        self.assertIs(cli.present_event_log_alert_check_command, cli_monitoring.present_event_log_alert_check_command)
        self.assertIs(cli.present_event_log_alerts_command, cli_monitoring.present_event_log_alerts_command)
        self.assertIs(cli.present_event_log_failures_command, cli_monitoring.present_event_log_failures_command)
        self.assertIs(cli.present_event_log_hotspots_command, cli_monitoring.present_event_log_hotspots_command)
        self.assertIs(cli.present_event_log_report_command, cli_monitoring.present_event_log_report_command)
        self.assertIs(cli.present_event_log_tail_command, cli_monitoring.present_event_log_tail_command)
        self.assertIs(cli.present_event_log_summary_command, cli_monitoring.present_event_log_summary_command)
        self.assertIs(cli.present_entity_index_command, cli_knowledge.present_entity_index_command)
        self.assertIs(cli.present_entity_relations_command, cli_knowledge.present_entity_relations_command)
        self.assertIs(cli.present_process_inbox_command, cli_knowledge.present_process_inbox_command)
        self.assertIs(cli.present_create_entity_command, cli_notes.present_create_entity_command)
        self.assertIs(cli.present_capture_command, cli_notes.present_capture_command)
        self.assertIs(cli.present_daily_status_command, cli_personal.present_daily_status_command)
        self.assertIs(cli.present_info_command, cli_system.present_info_command)
        self.assertIs(cli.load_event_log_path, cli_runtime.load_event_log_path)
        self.assertIs(cli.load_alert_output_dir, cli_runtime.load_alert_output_dir)
        self.assertIs(cli.load_event_sink, cli_runtime.load_event_sink)

        self.assertIn("present_alert_delivery_presets_command", exported)
        self.assertIn("build_alert_delivery_presets_table", exported)
        self.assertIn("present_event_log_alert_delivery_command", exported)
        self.assertIn("register_cli_commands", exported)
        self.assertIn("run_route_input_command", exported)
        self.assertIn("present_event_log_alert_message_command", exported)
        self.assertIn("present_event_log_alert_presets_command", exported)
        self.assertIn("present_event_log_alert_check_command", exported)
        self.assertIn("present_event_log_alerts_command", exported)
        self.assertIn("present_event_log_failures_command", exported)
        self.assertIn("present_event_log_hotspots_command", exported)
        self.assertIn("present_event_log_report_command", exported)
        self.assertIn("present_event_log_tail_command", exported)
        self.assertIn("present_event_log_summary_command", exported)
        self.assertIn("present_entity_index_command", exported)
        self.assertIn("present_entity_relations_command", exported)
        self.assertIn("present_process_inbox_command", exported)
        self.assertIn("present_create_entity_command", exported)
        self.assertIn("present_capture_command", exported)
        self.assertIn("present_daily_status_command", exported)
        self.assertIn("present_info_command", exported)
        self.assertIn("load_alert_output_dir", exported)
        self.assertIn("load_event_log_path", exported)
        self.assertIn("load_event_sink", exported)

    def test_conversation_exports_reuse_new_interface_modules(self) -> None:
        from brain_ops.interfaces.conversation import execution as conversation_execution
        from brain_ops.interfaces.conversation import follow_up as conversation_follow_up
        from brain_ops.interfaces.conversation import follow_up_state as conversation_follow_up_state
        from brain_ops.interfaces.conversation import handling as conversation_handling
        from brain_ops.interfaces.conversation import parsing_input as conversation_parsing_input
        from brain_ops.interfaces.conversation import routing_input as conversation_routing_input

        exported = set(conversation.__all__)

        self.assertIs(conversation.handle_input, conversation_handling.handle_input)
        self.assertIs(conversation.route_input, conversation_routing_input.route_input)
        self.assertIs(conversation.parse_intent, conversation_parsing_input.parse_intent)
        self.assertIs(conversation.execute_single_intent_result, conversation_execution.execute_single_intent_result)
        self.assertIs(conversation.apply_pending_follow_up, conversation_follow_up.apply_pending_follow_up)
        self.assertIs(conversation.PendingFollowUp, conversation_follow_up_state.PendingFollowUp)

        self.assertIn("handle_input", exported)
        self.assertIn("route_input", exported)
        self.assertIn("parse_intent", exported)
        self.assertIn("execute_single_intent_result", exported)
        self.assertIn("apply_pending_follow_up", exported)
        self.assertIn("PendingFollowUp", exported)

    def test_obsidian_exports_reuse_specialized_storage_modules(self) -> None:
        from brain_ops.storage.obsidian import note_loading
        from brain_ops.storage.obsidian import note_paths
        from brain_ops.storage.obsidian import note_writing
        from brain_ops.storage.obsidian import report_writing

        exported = set(obsidian.__all__)

        self.assertIs(obsidian.load_note_document, note_loading.load_note_document)
        self.assertIs(obsidian.relative_note_path, note_loading.relative_note_path)
        self.assertIs(obsidian.resolve_inbox_destination_path, note_paths.resolve_inbox_destination_path)
        self.assertIs(obsidian.write_note_document_if_changed, note_writing.write_note_document_if_changed)
        self.assertIs(obsidian.write_report_text, report_writing.write_report_text)

        self.assertIn("load_note_document", exported)
        self.assertIn("relative_note_path", exported)
        self.assertIn("resolve_inbox_destination_path", exported)
        self.assertIn("write_note_document_if_changed", exported)
        self.assertIn("write_report_text", exported)

    def test_sqlite_exports_reuse_specialized_storage_modules(self) -> None:
        from brain_ops.storage.sqlite import daily_summary
        from brain_ops.storage.sqlite import diets
        from brain_ops.storage.sqlite import follow_ups
        from brain_ops.storage.sqlite import goals
        from brain_ops.storage.sqlite import nutrition

        exported = set(sqlite.__all__)

        self.assertIs(sqlite.fetch_daily_summary_context_rows, daily_summary.fetch_daily_summary_context_rows)
        self.assertIs(sqlite.fetch_diet_plan_names, diets.fetch_diet_plan_names)
        self.assertIs(sqlite.upsert_follow_up, follow_ups.upsert_follow_up)
        self.assertIs(sqlite.upsert_macro_targets, goals.upsert_macro_targets)
        self.assertIs(sqlite.insert_meal_log, nutrition.insert_meal_log)

        self.assertIn("fetch_daily_summary_context_rows", exported)
        self.assertIn("fetch_diet_plan_names", exported)
        self.assertIn("upsert_follow_up", exported)
        self.assertIn("upsert_macro_targets", exported)
        self.assertIn("insert_meal_log", exported)


if __name__ == "__main__":
    import unittest

    unittest.main()
