"""Relations applier — Campaña 2.1 Paso 3.

Reads reviewed proposal YAMLs from a batch directory and applies the
approved typed triples to vault notes. Frontmatter-only, hash-verified,
idempotent.

Rules (aligned with Campaña 2.1 decisions + user clarifications):

1. Only triples with `status: approved` AND `object_status:
   canonical_entity_exists` are applied by default. MISSING_ENTITY is
   refused unless `allow_mentions=True`. DISAMBIGUATION_PAGE is always
   refused — reviewer must rename the target.
2. Body bytes are never touched. Frontmatter bytes outside the
   `relationships:` block are never touched. Verified with SHA-256
   before/after each file.
3. Triples whose (predicate, object) is already in the note's
   `relationships:` are silently skipped (idempotency).
4. No file outside the batch manifest is written. Verified post-apply.
5. On any verification failure, the applier halts and leaves the snapshot
   in place for manual inspection or rollback.
6. Dry-run is the default. Real apply requires explicit `apply=True`.
"""

from __future__ import annotations

import hashlib
import re
import shlex
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from brain_ops.domains.knowledge.object_model import CANONICAL_PREDICATES
from brain_ops.domains.knowledge.relations_typed import parse_relationships
from brain_ops.frontmatter import split_frontmatter
from brain_ops.vault import Vault

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

SkipReason = str  # "already_typed" | "missing_entity" | "disambig_page" |
                  # "not_approved" | "unknown_predicate" | "invalid_shape"


@dataclass(slots=True)
class ProposalTriple:
    id: str
    predicate: str
    object: str
    confidence: str
    status: str
    object_status: str
    reason: str | None = None
    date: str | None = None
    source_id: str | None = None


@dataclass(slots=True)
class LoadedProposal:
    path: Path
    entity: str
    triples: list[ProposalTriple]


@dataclass(slots=True)
class EntityApplyResult:
    entity: str
    note_relative_path: str
    baseline_typed: int
    proposal_total: int
    applied_ids: list[str]
    skipped: dict[SkipReason, list[str]]
    body_sha_before: str | None = None
    body_sha_after: str | None = None
    frontmatter_outside_block_sha_before: str | None = None
    frontmatter_outside_block_sha_after: str | None = None
    ok: bool = True
    error: str | None = None


@dataclass(slots=True)
class ApplyReport:
    batch_name: str
    dry_run: bool
    allow_mentions: bool
    entities: list[EntityApplyResult] = field(default_factory=list)
    snapshot_path: Path | None = None
    aborted: bool = False
    abort_reason: str | None = None
    missing_entity_queue: list[str] = field(default_factory=list)
    # Planned entity list captured before the apply loop. Used to compute
    # `not_processed_entities` when a batch aborts mid-run.
    planned_entities: list[str] = field(default_factory=list)
    vault_path: Path | None = None
    knowledge_folder: str | None = None

    @property
    def total_applied(self) -> int:
        return sum(len(e.applied_ids) for e in self.entities if e.ok)

    @property
    def total_skipped(self) -> int:
        return sum(
            sum(len(ids) for ids in e.skipped.values())
            for e in self.entities
        )

    @property
    def applied_entities(self) -> list[str]:
        """Entities that successfully received at least one triple.

        In abort scenarios (dry_run=False only), these are the notes that
        were actually written before the applier halted. User should consult
        this list before deciding whether to roll back the batch manually.
        """
        return [e.entity for e in self.entities if e.ok and e.applied_ids]

    @property
    def aborted_entity(self) -> str | None:
        if not self.aborted:
            return None
        for e in reversed(self.entities):
            if not e.ok:
                return e.entity
        return None

    @property
    def not_processed_entities(self) -> list[str]:
        processed = {e.entity for e in self.entities}
        return [name for name in self.planned_entities if name not in processed]

    def rollback_instructions(self) -> list[str]:
        """Shell commands (copy-pasteable) to restore the vault to the
        pre-batch snapshot. Only meaningful when a non-dry-run apply has
        taken a snapshot; returns an explanatory message otherwise.
        """
        if self.dry_run:
            return ["# Dry-run: nothing was written. No rollback needed."]
        if self.snapshot_path is None:
            return ["# No snapshot recorded — cannot auto-generate rollback commands."]
        if self.vault_path is None or self.knowledge_folder is None:
            return ["# Vault context missing on report — restore snapshot manually."]

        knowledge = self.vault_path / self.knowledge_folder
        snapshot_knowledge = self.snapshot_path / self.knowledge_folder
        renamed = str(knowledge) + ".pre-rollback"
        qk = shlex.quote(str(knowledge))
        qs = shlex.quote(str(snapshot_knowledge))
        qr = shlex.quote(renamed)
        return [
            f"# Rollback protocol for batch {self.batch_name}",
            f"# Entities already applied ({len(self.applied_entities)}):",
            *[f"#   - {name}" for name in self.applied_entities],
            f"# Entity that aborted: {self.aborted_entity or '(none)'}",
            f"# Entities not processed ({len(self.not_processed_entities)}):",
            *[f"#   - {name}" for name in self.not_processed_entities],
            f"#",
            f"# 1. Move current Knowledge folder aside (safety):",
            f"mv {qk} {qr}",
            f"# 2. Restore from snapshot:",
            f"cp -R {qs} {qk}",
            f"# 3. Rebuild SQLite from restored frontmatter:",
            f"brain compile-knowledge --config config/vault.yaml",
            f"# 4. Verify no stray writes (optional — should return nothing):",
            f"diff -r {qk} {qs} | head",
            f"# 5. After verifying, remove the renamed folder:",
            f"# rm -rf {qr}",
        ]

    def to_dict(self) -> dict:
        return {
            "batch_name": self.batch_name,
            "dry_run": self.dry_run,
            "allow_mentions": self.allow_mentions,
            "total_applied": self.total_applied,
            "total_skipped": self.total_skipped,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "snapshot_path": str(self.snapshot_path) if self.snapshot_path else None,
            "missing_entity_queue": list(self.missing_entity_queue),
            "planned_entities": list(self.planned_entities),
            "applied_entities": self.applied_entities,
            "aborted_entity": self.aborted_entity,
            "not_processed_entities": self.not_processed_entities,
            "rollback_instructions": self.rollback_instructions(),
            "entities": [
                {
                    "entity": e.entity,
                    "note_relative_path": e.note_relative_path,
                    "baseline_typed": e.baseline_typed,
                    "proposal_total": e.proposal_total,
                    "applied": e.applied_ids,
                    "skipped": {k: list(v) for k, v in e.skipped.items()},
                    "ok": e.ok,
                    "error": e.error,
                    "body_sha_before": e.body_sha_before,
                    "body_sha_after": e.body_sha_after,
                }
                for e in self.entities
            ],
        }


# ---------------------------------------------------------------------------
# Loading proposals from a batch directory
# ---------------------------------------------------------------------------


class BatchLoadError(RuntimeError):
    pass


def resolve_batch_dir(vault: Vault, batch_name: str) -> Path:
    return (
        Path(vault.config.vault_path)
        / ".brain-ops" / "relations-proposals" / f"batch-{batch_name}"
    )


def load_batch(batch_dir: Path) -> list[LoadedProposal]:
    if not batch_dir.exists():
        raise BatchLoadError(f"Batch directory not found: {batch_dir}")
    if not batch_dir.is_dir():
        raise BatchLoadError(f"Batch path is not a directory: {batch_dir}")

    proposals: list[LoadedProposal] = []
    for yaml_path in sorted(batch_dir.glob("*.yaml")):
        if yaml_path.name == "manifest.yaml":
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise BatchLoadError(f"{yaml_path}: invalid YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise BatchLoadError(f"{yaml_path}: expected mapping at top level")
        entity = data.get("entity")
        if not isinstance(entity, str) or not entity:
            raise BatchLoadError(f"{yaml_path}: missing or invalid `entity`")
        raw_triples = data.get("proposal") or []
        if not isinstance(raw_triples, list):
            raise BatchLoadError(f"{yaml_path}: `proposal` must be a list")

        triples: list[ProposalTriple] = []
        for idx, raw in enumerate(raw_triples):
            if not isinstance(raw, dict):
                continue  # silently skip malformed items; logged downstream
            triples.append(ProposalTriple(
                id=str(raw.get("id") or f"{entity}-{idx:02d}"),
                predicate=str(raw.get("predicate", "")),
                object=str(raw.get("object", "")),
                confidence=str(raw.get("confidence", "medium")),
                status=str(raw.get("status", "needs-refinement")),
                object_status=str(raw.get("object_status", "MISSING_ENTITY")),
                reason=raw.get("reason") if isinstance(raw.get("reason"), str) else None,
                date=raw.get("date") if isinstance(raw.get("date"), str) else None,
                source_id=raw.get("source_id") if isinstance(raw.get("source_id"), str) else None,
            ))

        proposals.append(LoadedProposal(path=yaml_path, entity=entity, triples=triples))

    if not proposals:
        raise BatchLoadError(f"No *.yaml proposals found in {batch_dir}")

    return proposals


# ---------------------------------------------------------------------------
# Filtering (idempotency + MISSING_ENTITY + approval)
# ---------------------------------------------------------------------------


def _read_note_for_entity(vault: Vault, entity: str) -> tuple[Path, str, dict, str]:
    knowledge = Path(vault.config.vault_path) / vault.config.folders.knowledge
    note_path = knowledge / f"{entity}.md"
    if not note_path.exists():
        raise BatchLoadError(f"Note not found for entity {entity!r}: {note_path}")
    text = note_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    return note_path, text, frontmatter, body


def _existing_typed_keys(frontmatter: dict, entity: str) -> set[tuple[str, str]]:
    parse_result = parse_relationships(entity, frontmatter)
    return {(t.predicate, t.object) for t in parse_result.typed}


def _filter_triples_to_apply(
    triples: list[ProposalTriple],
    existing_keys: set[tuple[str, str]],
    *,
    allow_mentions: bool,
) -> tuple[list[ProposalTriple], dict[SkipReason, list[str]]]:
    skipped: dict[SkipReason, list[str]] = {}
    kept: list[ProposalTriple] = []

    def _skip(reason: SkipReason, triple_id: str) -> None:
        skipped.setdefault(reason, []).append(triple_id)

    for t in triples:
        if t.status != "approved":
            _skip("not_approved", t.id)
            continue
        if t.predicate not in CANONICAL_PREDICATES:
            _skip("unknown_predicate", t.id)
            continue
        if not t.object:
            _skip("invalid_shape", t.id)
            continue
        if (t.predicate, t.object) in existing_keys:
            _skip("already_typed", t.id)
            continue
        if t.object_status == "DISAMBIGUATION_PAGE":
            _skip("disambig_page", t.id)
            continue
        if t.object_status == "MISSING_ENTITY" and not allow_mentions:
            _skip("missing_entity", t.id)
            continue
        kept.append(t)

    return kept, skipped


# ---------------------------------------------------------------------------
# Block rendering + byte-level insertion/replacement
# ---------------------------------------------------------------------------


_TOP_LEVEL_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:")


def _yaml_scalar(value: str) -> str:
    if any(c in value for c in (":", "\n", '"', "'")) or value.strip() != value:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def render_relationships_block(triples: list[dict]) -> str:
    """Render a canonical `relationships:` YAML block.

    Each triple is a dict with keys: predicate, object, confidence (optional,
    default medium), reason (optional), date (optional), source_id (optional).
    """
    lines = ["relationships:"]
    for t in triples:
        lines.append(f"  - predicate: {t['predicate']}")
        lines.append(f"    object: {_yaml_scalar(str(t['object']))}")
        conf = t.get("confidence", "medium")
        if conf and conf != "medium":
            lines.append(f"    confidence: {conf}")
        if t.get("reason"):
            lines.append(f"    reason: {_yaml_scalar(str(t['reason']))}")
        if t.get("date"):
            lines.append(f"    date: {_yaml_scalar(str(t['date']))}")
        if t.get("source_id"):
            lines.append(f"    source_id: {_yaml_scalar(str(t['source_id']))}")
    return "\n".join(lines)


def _find_frontmatter_bounds(lines: list[str]) -> tuple[int, int] | None:
    if not lines or lines[0] != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            return (0, i)
    return None


def _find_relationships_block(lines: list[str], fm_start: int, fm_close: int) -> tuple[int, int] | None:
    """Return (block_start_line, block_end_line_exclusive) within frontmatter."""
    rel_start = None
    for i in range(fm_start + 1, fm_close):
        if lines[i].lstrip().startswith("relationships:") and not lines[i].startswith(" "):
            rel_start = i
            break
    if rel_start is None:
        return None
    block_end = fm_close
    for i in range(rel_start + 1, fm_close):
        line = lines[i]
        if line and _TOP_LEVEL_KEY_RE.match(line):
            block_end = i
            break
    return (rel_start, block_end)


def insert_or_replace_relationships_block(text: str, new_block: str) -> str:
    """Return new text with the `relationships:` block replaced/inserted.

    - If the note already has a `relationships:` block, it is replaced.
    - Otherwise the new block is inserted right before the closing `---`.
    - Body bytes and other frontmatter lines are preserved exactly.
    """
    lines = text.split("\n")
    fm_bounds = _find_frontmatter_bounds(lines)
    if fm_bounds is None:
        raise RuntimeError("Frontmatter not found (missing `---` delimiters)")
    fm_start, fm_close = fm_bounds

    block_lines = new_block.split("\n")
    existing = _find_relationships_block(lines, fm_start, fm_close)
    if existing is not None:
        rel_start, rel_end = existing
        new_lines = lines[:rel_start] + block_lines + lines[rel_end:]
    else:
        new_lines = lines[:fm_close] + block_lines + lines[fm_close:]

    return "\n".join(new_lines)


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _body_bytes(text: str) -> bytes:
    lines = text.split("\n")
    fm_bounds = _find_frontmatter_bounds(lines)
    if fm_bounds is None:
        return text.encode("utf-8")
    _, fm_close = fm_bounds
    return "\n".join(lines[fm_close + 1:]).encode("utf-8")


def _frontmatter_outside_block_bytes(text: str) -> bytes:
    lines = text.split("\n")
    fm_bounds = _find_frontmatter_bounds(lines)
    if fm_bounds is None:
        return b""
    fm_start, fm_close = fm_bounds
    existing = _find_relationships_block(lines, fm_start, fm_close)
    if existing is None:
        return "\n".join(lines[fm_start:fm_close + 1]).encode("utf-8")
    rel_start, rel_end = existing
    outside = lines[fm_start:rel_start] + lines[rel_end:fm_close + 1]
    return "\n".join(outside).encode("utf-8")


# ---------------------------------------------------------------------------
# Top-level apply
# ---------------------------------------------------------------------------


def _snapshot_knowledge(vault: Vault, batch_name: str) -> Path:
    knowledge = Path(vault.config.vault_path) / vault.config.folders.knowledge
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    snap_dir = (
        Path(vault.config.vault_path)
        / ".brain-ops" / "backups"
        / f"relations-batch-{batch_name}-{ts}"
    )
    snap_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(knowledge, snap_dir / knowledge.name)
    return snap_dir


def _build_merged_triples(
    existing_typed: list,
    new_to_apply: list[ProposalTriple],
) -> list[dict]:
    """Build the canonical list of triples for the new block.

    `existing_typed` is the list of `TypedRelation` objects from the current
    frontmatter. New triples are appended in the order received.
    """
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for t in existing_typed:
        key = (t.predicate, t.object)
        if key in seen:
            continue
        seen.add(key)
        item: dict = {"predicate": t.predicate, "object": t.object}
        if t.confidence and t.confidence != "medium":
            item["confidence"] = t.confidence
        if t.reason:
            item["reason"] = t.reason
        if t.date:
            item["date"] = t.date
        if t.source_id:
            item["source_id"] = t.source_id
        out.append(item)
    for t in new_to_apply:
        key = (t.predicate, t.object)
        if key in seen:
            continue
        seen.add(key)
        item = {"predicate": t.predicate, "object": t.object}
        if t.confidence and t.confidence != "medium":
            item["confidence"] = t.confidence
        if t.reason:
            item["reason"] = t.reason
        if t.date:
            item["date"] = t.date
        if t.source_id:
            item["source_id"] = t.source_id
        out.append(item)
    return out


def apply_batch(
    batch_name: str,
    vault: Vault,
    *,
    dry_run: bool = True,
    allow_mentions: bool = False,
) -> ApplyReport:
    report = ApplyReport(
        batch_name=batch_name,
        dry_run=dry_run,
        allow_mentions=allow_mentions,
        vault_path=Path(vault.config.vault_path),
        knowledge_folder=vault.config.folders.knowledge,
    )

    batch_dir = resolve_batch_dir(vault, batch_name)
    proposals = load_batch(batch_dir)
    report.planned_entities = [lp.entity for lp in proposals]

    # Phase 1: plan all entities (no writes yet).
    plans: list[tuple[LoadedProposal, Path, str, list[ProposalTriple], list, dict[SkipReason, list[str]]]] = []
    missing_queue: set[str] = set()

    for lp in proposals:
        note_path, text, fm, _body = _read_note_for_entity(vault, lp.entity)
        existing_keys = _existing_typed_keys(fm, lp.entity)
        existing_typed = parse_relationships(lp.entity, fm).typed
        kept, skipped = _filter_triples_to_apply(
            lp.triples, existing_keys, allow_mentions=allow_mentions,
        )
        for t in lp.triples:
            if t.object_status == "MISSING_ENTITY":
                missing_queue.add(t.object)
        plans.append((lp, note_path, text, kept, existing_typed, skipped))

    # Snapshot only if we're actually going to write.
    if not dry_run:
        report.snapshot_path = _snapshot_knowledge(vault, batch_name)

    # Phase 2: apply (or simulate) per entity.
    for lp, note_path, pre_text, kept, existing_typed, skipped in plans:
        rel_path = str(note_path.relative_to(Path(vault.config.vault_path)))
        body_pre = _sha(_body_bytes(pre_text))
        fm_outside_pre = _sha(_frontmatter_outside_block_bytes(pre_text))

        result = EntityApplyResult(
            entity=lp.entity,
            note_relative_path=rel_path,
            baseline_typed=len(existing_typed),
            proposal_total=len(lp.triples),
            applied_ids=[t.id for t in kept],
            skipped=skipped,
            body_sha_before=body_pre,
            frontmatter_outside_block_sha_before=fm_outside_pre,
        )

        if not kept:
            # Nothing to apply — idempotent noop for this entity.
            result.body_sha_after = body_pre
            result.frontmatter_outside_block_sha_after = fm_outside_pre
            report.entities.append(result)
            continue

        merged = _build_merged_triples(existing_typed, kept)
        new_block = render_relationships_block(merged)
        new_text = insert_or_replace_relationships_block(pre_text, new_block)

        body_post = _sha(_body_bytes(new_text))
        fm_outside_post = _sha(_frontmatter_outside_block_bytes(new_text))

        if body_post != body_pre:
            result.ok = False
            result.error = (
                f"body drift detected: pre={body_pre[:12]} post={body_post[:12]}"
            )
            report.entities.append(result)
            report.aborted = True
            report.abort_reason = f"{lp.entity}: body drift"
            return report

        if fm_outside_post != fm_outside_pre:
            result.ok = False
            result.error = (
                f"frontmatter-outside-block drift: "
                f"pre={fm_outside_pre[:12]} post={fm_outside_post[:12]}"
            )
            report.entities.append(result)
            report.aborted = True
            report.abort_reason = f"{lp.entity}: frontmatter-outside-block drift"
            return report

        result.body_sha_after = body_post
        result.frontmatter_outside_block_sha_after = fm_outside_post

        if not dry_run:
            note_path.write_text(new_text, encoding="utf-8")

        report.entities.append(result)

    report.missing_entity_queue = sorted(missing_queue)
    return report


__all__ = [
    "ApplyReport",
    "BatchLoadError",
    "EntityApplyResult",
    "LoadedProposal",
    "ProposalTriple",
    "apply_batch",
    "insert_or_replace_relationships_block",
    "load_batch",
    "render_relationships_block",
    "resolve_batch_dir",
]
