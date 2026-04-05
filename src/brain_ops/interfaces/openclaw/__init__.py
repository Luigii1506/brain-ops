"""OpenClaw adapter layer."""

from .manifest import (
    OPENCLAW_MANIFEST,
    build_openclaw_manifest_table,
    serialize_openclaw_manifest,
    write_openclaw_manifest,
)

__all__ = [
    "OPENCLAW_MANIFEST",
    "build_openclaw_manifest_table",
    "serialize_openclaw_manifest",
    "write_openclaw_manifest",
]
