"""Batch proposer — Campaña 2.1 Paso 4.

Runs `propose_relations_for_entity` across a filtered set of vault notes
and materialises a batch directory ready for human review.

Output layout:

    <vault>/.brain-ops/relations-proposals/batch-<name>/
        ├── manifest.yaml         # immutable filter + per-entity stats
        ├── <entity>.yaml         # one file per entity (reviewer edits these)
        ├── missing_entities.md   # aggregated creation queue
        └── summary.md            # human-readable pivot table

Read-only with respect to the vault notes themselves. Only writes inside
`.brain-ops/relations-proposals/batch-<name>/`.

Per Campaña 2.1 clarification #1, missing entities are surfaced explicitly
in `missing_entities.md` with the triples that would be blocked.
Per Campaña 2.1 clarification #3, the `evidence.source` field in each
proposal is drawn from the closed enumeration
`{body, related, metadata, cross-ref}`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from brain_ops.domains.knowledge.relations_proposer import (
    ProposalResult,
    propose_relations_for_entity,
)
from brain_ops.domains.knowledge.relations_applier import resolve_batch_dir
from brain_ops.frontmatter import split_frontmatter
from brain_ops.storage.obsidian.note_listing import list_vault_markdown_notes
from brain_ops.vault import Vault


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BatchFilter:
    subtype: str | None = None
    domain: str | None = None
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    limit: int | None = None


@dataclass(slots=True)
class BatchEntityStat:
    name: str
    note_relative_path: str
    baseline_typed: int
    proposed: int
    high: int
    medium: int
    missing_count: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "note_relative_path": self.note_relative_path,
            "baseline_typed": self.baseline_typed,
            "proposed": self.proposed,
            "high": self.high,
            "medium": self.medium,
            "missing_count": self.missing_count,
        }


@dataclass(slots=True)
class BatchBuildResult:
    batch_name: str
    batch_dir: Path
    created_at: str
    filter_: BatchFilter
    entities: list[BatchEntityStat] = field(default_factory=list)
    missing_queue: dict[str, list[str]] = field(default_factory=dict)
    skipped_empty: list[str] = field(default_factory=list)

    @property
    def totals(self) -> dict[str, int]:
        return {
            "entities": len(self.entities),
            "triples_proposed": sum(e.proposed for e in self.entities),
            "triples_high": sum(e.high for e in self.entities),
            "triples_medium": sum(e.medium for e in self.entities),
            "missing_entity_candidates": len(self.missing_queue),
        }

    def to_dict(self) -> dict:
        return {
            "batch_name": self.batch_name,
            "batch_dir": str(self.batch_dir),
            "created_at": self.created_at,
            "filter": {
                "subtype": self.filter_.subtype,
                "domain": self.filter_.domain,
                "include": list(self.filter_.include),
                "exclude": list(self.filter_.exclude),
                "limit": self.filter_.limit,
            },
            "entities": [e.to_dict() for e in self.entities],
            "skipped_empty": list(self.skipped_empty),
            "missing_queue": {k: list(v) for k, v in self.missing_queue.items()},
            "totals": self.totals,
        }


class BatchBuildError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Candidate enumeration
# ---------------------------------------------------------------------------


def enumerate_candidate_entities(
    vault: Vault,
    filter_: BatchFilter,
) -> list[str]:
    include_set = set(filter_.include) if filter_.include else None
    exclude_set = set(filter_.exclude)

    matched: list[str] = []
    for path in list_vault_markdown_notes(vault):
        try:
            text = path.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(text)
        except Exception:
            continue
        name = fm.get("name")
        if not isinstance(name, str):
            continue
        if fm.get("entity") is not True:
            continue
        if fm.get("object_kind") == "disambiguation_page":
            continue
        if name in exclude_set:
            continue
        if include_set is not None and name not in include_set:
            continue
        if filter_.subtype is not None and fm.get("subtype") != filter_.subtype:
            continue
        if filter_.domain is not None:
            note_domain = fm.get("domain")
            if isinstance(note_domain, list):
                if filter_.domain not in note_domain:
                    continue
            elif note_domain != filter_.domain:
                continue
        matched.append(name)

    # Deterministic ordering — matters for reproducible batch manifests.
    matched.sort()
    if filter_.limit is not None:
        matched = matched[: filter_.limit]
    return matched


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def _write_manifest(batch_dir: Path, result: BatchBuildResult) -> Path:
    path = batch_dir / "manifest.yaml"
    payload = {
        "batch_name": result.batch_name,
        "created_at": result.created_at,
        "filter": {
            "subtype": result.filter_.subtype,
            "domain": result.filter_.domain,
            "include": list(result.filter_.include),
            "exclude": list(result.filter_.exclude),
            "limit": result.filter_.limit,
        },
        "entities": [e.to_dict() for e in result.entities],
        "skipped_empty": list(result.skipped_empty),
        "totals": result.totals,
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _write_missing_entities_md(batch_dir: Path, result: BatchBuildResult) -> Path:
    path = batch_dir / "missing_entities.md"
    lines: list[str] = [
        f"# Missing entities — batch {result.batch_name}",
        "",
        "Objects referenced by proposed triples that do NOT exist as",
        "canonical entities in the vault. These triples are emitted in",
        "the proposals (auditable) but `brain apply-relations-batch`",
        "refuses to apply them unless `--allow-mentions` is explicit.",
        "",
        f"Generated: {result.created_at}",
        f"Total missing: {len(result.missing_queue)}",
        "",
    ]

    # Group by reference count — more references → higher priority for creation
    by_ref = sorted(
        result.missing_queue.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    if by_ref:
        lines.append("## Ranked by reference count")
        lines.append("")
        for target, refs in by_ref:
            if len(refs) > 1:
                lines.append(f"- **{target}** — {len(refs)} refs: {', '.join(sorted(refs))}")
        if not any(len(refs) > 1 for _, refs in by_ref):
            lines.append("_(No target is referenced by more than one note in this batch.)_")
        lines.append("")

    lines.append("## All missing entities")
    lines.append("")
    for target, refs in sorted(result.missing_queue.items()):
        lines.append(f"- `{target}` — referenced by: {', '.join(sorted(refs))}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_summary_md(batch_dir: Path, result: BatchBuildResult) -> Path:
    path = batch_dir / "summary.md"
    lines: list[str] = [
        f"# Batch {result.batch_name} — summary",
        "",
        f"Created: {result.created_at}",
        f"Filter: subtype={result.filter_.subtype or '—'}, "
        f"domain={result.filter_.domain or '—'}, "
        f"limit={result.filter_.limit if result.filter_.limit is not None else '—'}",
        "",
        "| Entity | Baseline typed | Proposed | High | Medium | Missing |",
        "|--------|---------------:|---------:|-----:|-------:|--------:|",
    ]
    for e in result.entities:
        lines.append(
            f"| {e.name} | {e.baseline_typed} | {e.proposed} | "
            f"{e.high} | {e.medium} | {e.missing_count} |"
        )

    totals = result.totals
    lines.extend([
        "",
        f"**Totals**: {totals['entities']} entities, "
        f"{totals['triples_proposed']} triples "
        f"({totals['triples_high']} high, {totals['triples_medium']} medium), "
        f"{totals['missing_entity_candidates']} missing entity candidates.",
        "",
    ])

    if result.skipped_empty:
        lines.append("## Skipped — no new proposals after filter")
        lines.append("")
        for name in result.skipped_empty:
            lines.append(f"- {name}")
        lines.append("")

    lines.extend([
        "## Next steps",
        "",
        "1. Review each `<entity>.yaml` in this directory.",
        "2. Flip `status: approved|rejected|needs-refinement` per triple.",
        "3. Dry-run: `brain apply-relations-batch " + result.batch_name + " --config config/vault.yaml`",
        "4. Apply: `brain apply-relations-batch " + result.batch_name + " --config config/vault.yaml --apply`",
        "5. (optional) `brain compile-knowledge --config config/vault.yaml`",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_entity_proposal(
    batch_dir: Path,
    batch_name: str,
    proposal: ProposalResult,
) -> Path:
    payload = proposal.to_yaml_dict()
    payload["batch"] = batch_name
    path = batch_dir / f"{proposal.entity}.yaml"
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_batch(
    vault: Vault,
    batch_name: str,
    filter_: BatchFilter,
    *,
    skip_empty: bool = True,
    overwrite: bool = False,
    mode: str = "cheap",
    llm_client: object | None = None,
    cache_dir: Path | None = None,
) -> BatchBuildResult:
    """Construye un batch de proposals. Campaña 2.2B Paso 5: `mode`,
    `llm_client`, `cache_dir` se pasan through a `propose_relations_for_entity`.
    Default mode="cheap" preserva el comportamiento pre-2.2B.
    """
    batch_dir = resolve_batch_dir(vault, batch_name)
    if batch_dir.exists():
        if not overwrite:
            raise BatchBuildError(
                f"Batch directory already exists: {batch_dir}. "
                f"Pass overwrite=True to replace it."
            )
        import shutil
        shutil.rmtree(batch_dir)
    batch_dir.mkdir(parents=True)

    db_path = Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db"
    candidates = enumerate_candidate_entities(vault, filter_)

    result = BatchBuildResult(
        batch_name=batch_name,
        batch_dir=batch_dir,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        filter_=filter_,
    )

    for name in candidates:
        try:
            proposal = propose_relations_for_entity(
                name, vault,
                db_path=db_path if db_path.exists() else None,
                mode=mode,
                llm_client=llm_client,
                cache_dir=cache_dir,
            )
        except FileNotFoundError:
            # Entity enumerated but note missing (race condition) — skip.
            continue

        if skip_empty and not proposal.proposal:
            result.skipped_empty.append(name)
            continue

        # Write per-entity YAML
        note_path = _find_note_rel_path(vault, name)
        _write_entity_proposal(batch_dir, batch_name, proposal)

        # Stat row
        stat = BatchEntityStat(
            name=name,
            note_relative_path=note_path,
            baseline_typed=proposal.baseline.typed,
            proposed=len(proposal.proposal),
            high=sum(1 for p in proposal.proposal if p.confidence == "high"),
            medium=sum(1 for p in proposal.proposal if p.confidence == "medium"),
            missing_count=len(proposal.missing_entities_if_approved),
        )
        result.entities.append(stat)

        # Aggregate missing queue
        for miss in proposal.missing_entities_if_approved:
            result.missing_queue.setdefault(miss, []).append(name)

    _write_manifest(batch_dir, result)
    _write_missing_entities_md(batch_dir, result)
    _write_summary_md(batch_dir, result)

    return result


def _find_note_rel_path(vault: Vault, entity_name: str) -> str:
    knowledge = Path(vault.config.vault_path) / vault.config.folders.knowledge
    path = knowledge / f"{entity_name}.md"
    if path.exists():
        return str(path.relative_to(Path(vault.config.vault_path)))
    for candidate in list_vault_markdown_notes(vault):
        if candidate.stem == entity_name:
            return str(candidate.relative_to(Path(vault.config.vault_path)))
    return f"<unknown>/{entity_name}.md"


__all__ = [
    "BatchBuildError",
    "BatchBuildResult",
    "BatchEntityStat",
    "BatchFilter",
    "build_batch",
    "enumerate_candidate_entities",
]
