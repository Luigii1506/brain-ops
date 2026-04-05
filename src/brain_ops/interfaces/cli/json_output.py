"""Helpers for CLI JSON output."""

from __future__ import annotations

from typing import Protocol

from rich.console import Console


class JsonRenderable(Protocol):
    def model_dump_json(self, *, indent: int | None = None) -> str: ...


def print_model_json(console: Console, value: JsonRenderable) -> None:
    console.print_json(value.model_dump_json(indent=2))


def print_optional_model_json(console: Console, value: JsonRenderable | None) -> None:
    console.print_json("null" if value is None else value.model_dump_json(indent=2))


__all__ = ["print_model_json", "print_optional_model_json"]
