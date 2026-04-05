from __future__ import annotations

from brain_ops.models import HandleInputResult, RouteDecisionResult


def render_route_decision(result: RouteDecisionResult) -> str:
    lines = [
        "# Route Decision",
        "",
        f"- domain: {result.domain}",
        f"- command: {result.command}",
        f"- confidence: {result.confidence:.2f}",
        f"- routing_source: {result.routing_source}",
        f"- reason: {result.reason}",
        "",
        "## Extracted fields",
        "",
    ]
    if result.extracted_fields:
        for key, value in result.extracted_fields.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_handle_input(result: HandleInputResult) -> str:
    lines = [
        "# Handle Input",
        "",
        f"- executed: {str(result.executed).lower()}",
        f"- intent: {result.intent or '-'}",
        f"- intent_version: {result.intent_version or '-'}",
        f"- domain: {result.target_domain or result.decision.domain}",
        f"- command: {result.executed_command or result.decision.command}",
        f"- confidence: {(result.confidence if result.confidence is not None else result.decision.confidence):.2f}",
        f"- routing_source: {result.routing_source or result.decision.routing_source}",
        f"- needs_follow_up: {str(result.needs_follow_up).lower()}",
        f"- reason: {result.reason}",
        "",
    ]
    if result.extracted_fields:
        lines.extend(["## Extracted Fields", ""])
        for key, value in result.extracted_fields.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    if result.normalized_fields:
        lines.extend(["## Normalized Fields", ""])
        for key, value in result.normalized_fields.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    if result.assistant_message:
        lines.extend(["## Assistant Message", "", f"- {result.assistant_message}", ""])
    if result.sub_results:
        lines.extend(["## Sub Results", ""])
        for sub_result in result.sub_results:
            lines.append(
                f"- `{sub_result.input_text}` | executed={str(sub_result.executed).lower()} | "
                f"intent={sub_result.intent or '-'} | command={sub_result.executed_command or '-'} | "
                f"domain={sub_result.target_domain or '-'} | confidence={sub_result.confidence if sub_result.confidence is not None else '-'}"
            )
            if sub_result.normalized_fields:
                for key, value in sub_result.normalized_fields.items():
                    lines.append(f"  {key}: {value}")
        lines.append("")
    if result.follow_up:
        lines.extend(["## Follow up", "", f"- {result.follow_up}", ""])
    if result.follow_up_options:
        lines.extend(["## Follow up Options", ""])
        for option in result.follow_up_options:
            lines.append(f"- {option}")
        lines.append("")
    return "\n".join(lines)
