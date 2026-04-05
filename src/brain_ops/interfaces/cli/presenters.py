"""Presentation helpers for CLI command output."""

from __future__ import annotations

from typing import Iterable

from rich.console import Console, RenderableType

from brain_ops.models import OperationRecord

from .json_output import print_model_json, print_optional_model_json
from .tables import build_operations_table


def print_operations(console: Console, operations: list[OperationRecord]) -> None:
    console.print(build_operations_table(operations))


def print_rendered_with_operations(
    console: Console,
    operations: list[OperationRecord],
    rendered: RenderableType,
) -> None:
    print_operations(console, operations)
    console.print(rendered)


def print_rendered_with_single_operation(
    console: Console,
    operation: OperationRecord,
    rendered: RenderableType,
) -> None:
    print_rendered_with_operations(console, [operation], rendered)


def print_lines_with_single_operation(
    console: Console,
    operation: OperationRecord,
    lines: Iterable[str],
) -> None:
    print_operations(console, [operation])
    for line in lines:
        console.print(line)


def print_json_or_rendered(
    console: Console,
    *,
    as_json: bool,
    value: object,
    rendered: RenderableType,
) -> None:
    if as_json:
        print_model_json(console, value)  # type: ignore[arg-type]
        return
    console.print(rendered)


def print_optional_json_or_rendered(
    console: Console,
    *,
    as_json: bool,
    value: object | None,
    rendered: RenderableType,
) -> None:
    if as_json:
        print_optional_model_json(console, value)  # type: ignore[arg-type]
        return
    console.print(rendered)


def print_json_or_rendered_with_operations(
    console: Console,
    *,
    as_json: bool,
    value: object,
    rendered: RenderableType,
    operations: list[OperationRecord],
) -> None:
    if as_json:
        print_model_json(console, value)  # type: ignore[arg-type]
        return
    if operations:
        print_operations(console, operations)
    console.print(rendered)


def print_handle_input_result(
    console: Console,
    *,
    as_json: bool,
    result: object,
    rendered: RenderableType,
    operations: list[OperationRecord],
) -> None:
    if as_json:
        print_model_json(console, result)  # type: ignore[arg-type]
        return
    if operations:
        print_operations(console, operations)
    console.print(rendered)


__all__ = [
    "print_lines_with_single_operation",
    "print_handle_input_result",
    "print_json_or_rendered",
    "print_json_or_rendered_with_operations",
    "print_optional_json_or_rendered",
    "print_operations",
    "print_rendered_with_operations",
    "print_rendered_with_single_operation",
]
