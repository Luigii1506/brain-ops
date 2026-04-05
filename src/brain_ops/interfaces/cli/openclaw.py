"""CLI orchestration helpers for OpenClaw-facing commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import execute_openclaw_manifest_workflow
from brain_ops.interfaces.openclaw import (
    OPENCLAW_MANIFEST,
    build_openclaw_manifest_table,
    write_openclaw_manifest,
)


def present_openclaw_manifest(console: Console, *, as_json: bool, output: Path | None) -> None:
    output_path = execute_openclaw_manifest_workflow(
        output=output,
        write_manifest=write_openclaw_manifest,
    )
    if output_path is not None:
        console.print(f"Wrote OpenClaw manifest to {output_path}")
        if not as_json:
            return
    if as_json:
        console.print_json(data=OPENCLAW_MANIFEST)
        return
    console.print(build_openclaw_manifest_table())


__all__ = ["present_openclaw_manifest"]
