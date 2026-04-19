"""Relations proposer — Campaña 2.1 Paso 2.

Read-only analyzer that proposes typed triples for a single entity. Pattern-
based extraction (no LLM). Output is a YAML proposal file that a human
reviews, edits, and then feeds into `brain apply-relations-batch`.

Rules this module enforces:

1. Never writes to the vault note. Only emits a proposal file under
   `.brain-ops/relations-proposals/`.
2. Every proposed triple carries `evidence.source` drawn from the closed
   enumeration `{body, related, metadata, cross-ref}` (one or more).
3. `confidence` is exactly `high` or `medium`. Low-confidence candidates
   are NOT emitted — they stay in `related:` as legacy.
4. `high` triples default to `status: approved`. `medium` triples default
   to `status: needs-refinement` (must be manually approved before apply).
5. Objects are classified: `canonical_entity_exists` /
   `DISAMBIGUATION_PAGE` / `MISSING_ENTITY`. A high-confidence triple with
   `MISSING_ENTITY` is still emitted and clearly flagged — the downstream
   apply step refuses to write it unless `--allow-mentions` is explicit
   (per Campaña 2.1 clarification #1).
6. Triples already present in the note's `relationships:` are excluded
   from the proposal unless `--include-existing` is passed.
7. No inverse auto-generation. Cross-ref is evidence only — if another
   note has `mentor_of X`, we may boost confidence of a `studied_under`
   proposal on X's note, but we never auto-emit the inverse edge on X's
   note from the other note's edge.
"""

from __future__ import annotations

import functools
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

from brain_ops.domains.knowledge.object_model import CANONICAL_PREDICATES
from brain_ops.domains.knowledge.relations_typed import parse_relationships
from brain_ops.frontmatter import split_frontmatter
from brain_ops.storage.obsidian.note_listing import list_vault_markdown_notes
from brain_ops.vault import Vault

# ---------------------------------------------------------------------------
# Canonical enumerations
# ---------------------------------------------------------------------------

EVIDENCE_SOURCES: tuple[str, ...] = ("body", "related", "metadata", "cross-ref")
_VALID_SOURCES = frozenset(EVIDENCE_SOURCES)

ObjectStatus = Literal[
    "canonical_entity_exists",
    "DISAMBIGUATION_PAGE",
    "MISSING_ENTITY",
]

Confidence = Literal["high", "medium"]
Status = Literal["approved", "needs-refinement", "rejected"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenceExcerpt:
    location: str
    text: str


@dataclass(slots=True)
class ProposedRelation:
    id: str
    predicate: str
    object: str
    confidence: Confidence
    status: Status
    evidence_source: list[str]
    evidence_excerpts: list[EvidenceExcerpt]
    object_status: ObjectStatus
    note: str | None = None

    def to_yaml_dict(self) -> dict:
        for src in self.evidence_source:
            if src not in _VALID_SOURCES:
                raise ValueError(f"Invalid evidence source: {src!r}")
        out: dict = {
            "id": self.id,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "status": self.status,
            "evidence": {
                "source": list(self.evidence_source),
                "excerpts": [
                    {"location": e.location, "text": e.text}
                    for e in self.evidence_excerpts
                ],
            },
            "object_status": self.object_status,
        }
        if self.note:
            out["note"] = self.note
        return out


@dataclass(frozen=True, slots=True)
class ProposalBaseline:
    typed: int
    legacy_related: int
    body_chars: int


@dataclass(slots=True)
class ProposalResult:
    entity: str
    subtype: str | None
    domain: str | list[str] | None
    baseline: ProposalBaseline
    proposal: list[ProposedRelation]
    missing_entities_if_approved: list[str]
    notes_from_proposer: str
    generated_at: str
    batch: str | None = None

    def to_yaml_dict(self) -> dict:
        return {
            "batch": self.batch,
            "entity": self.entity,
            "subtype": self.subtype,
            "domain": self.domain,
            "generated_at": self.generated_at,
            "baseline": {
                "typed": self.baseline.typed,
                "legacy_related": self.baseline.legacy_related,
                "body_chars": self.baseline.body_chars,
            },
            "proposal": [p.to_yaml_dict() for p in self.proposal],
            "missing_entities_if_approved": list(self.missing_entities_if_approved),
            "notes_from_proposer": self.notes_from_proposer,
        }


# ---------------------------------------------------------------------------
# Body-pattern triggers
# ---------------------------------------------------------------------------
#
# Each entry: (predicate, trigger phrases, window_before_chars).
# A wikilink `[[X]]` is matched against this predicate if any trigger phrase
# appears within `window_before_chars` characters immediately preceding the
# wikilink. Triggers are case-insensitive. Only predicates in
# CANONICAL_PREDICATES may appear.

_BODY_TRIGGERS: list[tuple[str, tuple[str, ...], int]] = [
    ("child_of", ("hijo de", "hija de", "son of", "daughter of"), 40),
    ("parent_of", ("padre de", "madre de", "father of", "mother of"), 40),
    ("sibling_of", ("hermano de", "hermana de", "brother of", "sister of"), 40),
    ("married_to", (
        "esposo de", "esposa de", "casado con", "casada con",
        "husband of", "wife of", "married to",
    ), 40),
    ("studied_under", (
        "alumno de", "discípulo de", "estudió con", "estudió bajo",
        "estudiante de", "pupil of", "student of",
        "studied under", "studied with",
    ), 60),
    ("mentor_of", (
        "tutor de", "maestro de", "mentor de",
        "teacher of", "tutor of",
    ), 40),
    ("author_of", (
        "autor de", "autora de", "escribió",
        "author of", "wrote",
    ), 50),
    ("founded", (
        "fundó", "founded", "established",
        # Nominal forms — Campaña 2.1 mini-subfase trigger expansion.
        # Cover biographical prose like "Parménides, fundador de la escuela eleática".
        "fundador de", "fundadora de", "founder of",
    ), 40),
    ("conquered", ("conquistó", "conquered"), 40),
    ("ruled", (
        "rey de", "reina de", "emperador de", "emperatriz de", "gobernó",
        "king of", "queen of", "emperor of", "ruled",
    ), 40),
    ("fought_in", ("combatió en", "luchó en", "fought in", "fought at"), 40),
    ("born_in", (
        "nacido en", "nacida en", "nació en", "nacimiento en",
        "born in",
    ), 60),
    ("died_in", ("murió en", "falleció en", "died in"), 50),
    ("influenced_by", (
        "influenciado por", "influenciada por",
        "influido por", "influida por",
        "influenced by",
    ), 50),
    ("influenced", ("influyó en", "influyó a", "influenced"), 40),
    ("reacted_against", (
        "criticó a", "se opuso a", "reaccionó contra",
        "reacted against", "criticized",
    ), 50),
    ("opposed", (
        "rival de", "enemigo de", "adversario de",
        "enemy of", "adversary of",
    ), 50),
    ("allied_with", ("aliado de", "aliada de", "alianza con", "allied with"), 40),
    ("member_of", ("miembro de", "member of"), 40),
    ("appears_in", ("aparece en", "appears in"), 40),
    # Campaña 2.1 mini-subfase #2: nominal triggers for succession + adoption.
    # Decided conservatively: only the unambiguous forms. `hijastro de` deferred
    # because mapping to adopted_by vs child_of is a policy decision that needs
    # its own round.
    ("succeeded", ("sucesor de", "sucesora de"), 40),
    ("adopted_by", ("adoptado por", "adoptada por"), 40),
]

# Hedging words — presence in the same sentence downgrades HIGH to MEDIUM.
_HEDGING_MARKERS: tuple[str, ...] = (
    "indirectamente", "aparentemente", "probablemente",
    "se dice", "se cree", "podría", "quizá", "quizás",
    "indirecta", "indirecto",
)

_WIKILINK_RE = re.compile(r"\[\[([^\]\n|]+?)(?:\|[^\]\n]*)?\]\]")


def _validate_triggers() -> None:
    """Guard: every predicate in _BODY_TRIGGERS must be canonical."""
    for predicate, _, _ in _BODY_TRIGGERS:
        if predicate not in CANONICAL_PREDICATES:
            raise RuntimeError(
                f"relations_proposer: non-canonical predicate in triggers: {predicate!r}"
            )


_validate_triggers()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def _label_for_offset(body: str, offset: int) -> str:
    """Return a human-readable location label like `body.identity.line_12`."""
    # Walk back to find the nearest `## Section` header.
    prefix = body[:offset]
    section_match = None
    for m in re.finditer(r"^##\s+(.+?)$", prefix, re.MULTILINE):
        section_match = m
    line_no = prefix.count("\n") + 1
    if section_match:
        section = section_match.group(1).strip().lower().replace(" ", "_")
        return f"body.{section}.L{line_no}"
    return f"body.preamble.L{line_no}"


def _nearest_sentence(body: str, offset: int, span: int = 180) -> str:
    """Return a short excerpt around `offset` for evidence."""
    start = max(0, offset - span // 2)
    end = min(len(body), offset + span // 2)
    excerpt = body[start:end].strip()
    excerpt = re.sub(r"\s+", " ", excerpt)
    if len(excerpt) > span:
        excerpt = excerpt[:span] + "…"
    return excerpt


def _extract_wikilink_target(raw: str) -> str:
    """Strip wikilink brackets and pipe aliases; return canonical target."""
    core = raw.strip()
    if core.startswith("[[") and core.endswith("]]"):
        core = core[2:-2]
    if "|" in core:
        core = core.split("|", 1)[0]
    return core.strip()


def _find_trigger_in_window(trigger: str, window_lower: str) -> int | None:
    """Locate the rightmost occurrence of `trigger` inside `window_lower`.

    Returns the offset (within `window_lower`) of the match start, or None
    if the trigger does not appear.

    Campaña 2.2A Paso 3: dispatch between two strategies:
    - **Single-word triggers** (no whitespace): exact `str.rfind`.
      Verbos como "fundó", "founded", "wrote" no admiten intercalación
      útil — se quedan como están.
    - **Multi-word triggers** (contienen espacio): regex-tolerant matching
      construido por `_build_regex_for_trigger`. Acepta hasta
      `_MAX_INTERMEDIATE_TOKENS` palabras intermedias (adverbios/
      adjetivos) entre los tokens literales, con word boundaries en los
      extremos y puntuación como cortador de cláusula.

    Backwards compat: para cualquier trigger multi-palabra y un
    `window_lower` donde los tokens aparecen contiguos (sin intercalación),
    el regex produce la misma posición de match que `str.rfind`. Los
    ~30 tests existentes de `_extract_from_body` siguen pasando sin
    modificación.

    `trigger` asumido lowercased por el caller; `window_lower` también.
    El regex se construye case-insensitive por defecto (el caller podría
    en el futuro pasar texto no-normalizado sin romper el matching).
    """
    if " " in trigger:
        regex = _build_regex_for_trigger(trigger, _MAX_INTERMEDIATE_TOKENS)
        matches = list(regex.finditer(window_lower))
        if not matches:
            return None
        return matches[-1].start()  # rightmost, semantic equivalente a rfind
    # Single-word path (e.g. verbs): exact string search.
    idx = window_lower.rfind(trigger)
    return idx if idx >= 0 else None


# ---------------------------------------------------------------------------
# Regex matcher for multi-word triggers — Campaña 2.2A Paso 2
# ---------------------------------------------------------------------------
#
# Pure function. NOT wired to `_extract_from_body` yet. Paso 3 will integrate
# it behind a simple dispatch: "trigger contains space -> use regex; else
# keep str.find". For now this exists, is tested, and is callable in
# isolation.

# Upper bound on number of intermediate tokens (adverbs / adjectives)
# allowed between the literal tokens of a trigger. Chosen conservatively
# per the plan (D1 = 2). Lowering to 1 is the first escape hatch if the
# benchmark shows FPs from cross-clause matches.
_MAX_INTERMEDIATE_TOKENS: int = 2


@functools.lru_cache(maxsize=256)
def _build_regex_for_trigger(phrase: str, max_intermediate: int) -> re.Pattern:
    """Build a regex that matches a multi-word trigger with optional
    adverbs/adjectives intercalated between its literal tokens.

    Only multi-word triggers use this path. Single-word triggers (verbs
    like "fundó", "founded", "conquered") stay on `str.rfind` — there is
    nothing to intercalate for them.

    Between consecutive literal tokens, the regex allows 0 to
    `max_intermediate` intermediate `\\w+` tokens, each separated by
    whitespace. Word boundaries (`\\b`) guard both ends to prevent
    substring matches (e.g. `"sucesor de"` must not match inside
    `"predecesor de"`). Match is case-insensitive so the caller does not
    have to lowercase the input first when reaching the regex path.

    Punctuation between tokens (commas, semicolons, dashes) is NOT
    permitted intercalation — `\\w+` only covers word characters, so
    any non-word character breaks the match. This is intentional: a
    comma likely indicates a clause boundary and the match would likely
    cross to a different grammatical subject.

    The function is cached because a small, fixed number of multi-word
    trigger phrases get compiled once per process.

    Examples (illustrative, with max_intermediate=2):
        _build_regex_for_trigger("sucesor de", 2)
        → compiled /\\bsucesor(?:\\s+\\w+){0,2}\\s+de\\b/i
        _build_regex_for_trigger("fundador de", 2)
        → compiled /\\bfundador(?:\\s+\\w+){0,2}\\s+de\\b/i
    """
    tokens = phrase.split()
    if len(tokens) < 2:
        raise ValueError(
            f"_build_regex_for_trigger requires a multi-word trigger "
            f"(got {phrase!r}); single-word triggers should use str.rfind"
        )
    if max_intermediate < 0:
        raise ValueError(
            f"max_intermediate must be >= 0 (got {max_intermediate})"
        )

    escaped_tokens = [re.escape(t) for t in tokens]
    # Connector between consecutive tokens: 0 to N intermediate "\s+\w+"
    # slots, then the required final "\s+".
    connector = rf"(?:\s+\w+){{0,{max_intermediate}}}\s+"
    pattern = r"\b" + connector.join(escaped_tokens) + r"\b"
    return re.compile(pattern, re.IGNORECASE)


def _extract_from_body(
    entity_name: str, body: str
) -> list[ProposedRelation]:
    """Scan body for `<trigger> <wikilink>` patterns."""
    out: list[ProposedRelation] = []
    seen: set[tuple[str, str]] = set()

    for m in _WIKILINK_RE.finditer(body):
        target = _extract_wikilink_target(m.group(0))
        if not target or target == entity_name:
            continue
        target_offset = m.start()
        preceding = body[:target_offset]

        # Find closest trigger across all predicates; pick the one with
        # highest offset (closest to wikilink).
        best: tuple[int, str, str] | None = None  # (offset, predicate, trigger)
        preceding_lower = preceding.lower()
        for predicate, triggers, window in _BODY_TRIGGERS:
            slice_start = max(0, target_offset - window)
            preceding_window_lower = preceding_lower[slice_start:target_offset]
            for trigger in triggers:
                idx = _find_trigger_in_window(trigger, preceding_window_lower)
                if idx is None:
                    continue
                absolute_offset = slice_start + idx
                if best is None or absolute_offset > best[0]:
                    best = (absolute_offset, predicate, trigger)
                    break  # first matching trigger in this predicate is enough

        if best is None:
            continue

        _, predicate, trigger = best
        key = (predicate, target)
        if key in seen:
            continue
        seen.add(key)

        # Detect hedging markers in the sentence enclosing the match.
        sentence_start = max(
            preceding.rfind(".", 0, target_offset),
            preceding.rfind("\n", 0, target_offset),
        )
        sentence_start = max(sentence_start + 1, 0)
        sentence_end = body.find(".", target_offset)
        if sentence_end < 0:
            sentence_end = min(len(body), target_offset + 200)
        sentence = body[sentence_start:sentence_end].lower()
        hedged = any(hedge in sentence for hedge in _HEDGING_MARKERS)

        confidence: Confidence = "medium" if hedged else "high"
        status: Status = "approved" if confidence == "high" else "needs-refinement"

        excerpt = _nearest_sentence(body, target_offset)
        location = _label_for_offset(body, target_offset)

        out.append(ProposedRelation(
            id="",  # assigned later
            predicate=predicate,
            object=target,
            confidence=confidence,
            status=status,
            evidence_source=["body"],
            evidence_excerpts=[EvidenceExcerpt(location=location, text=excerpt)],
            object_status="canonical_entity_exists",  # filled later
        ))

    return out


def _extract_from_metadata(
    entity_name: str, frontmatter: dict
) -> list[ProposedRelation]:
    """Derive triples from specific frontmatter fields."""
    out: list[ProposedRelation] = []

    occupation = frontmatter.get("occupation")
    if isinstance(occupation, str):
        # Patterns like "Rey de Macedonia", "Emperador romano"
        for predicate_label, canonical in (
            ("rey de ", "ruled"), ("reina de ", "ruled"),
            ("emperador de ", "ruled"), ("emperatriz de ", "ruled"),
            ("king of ", "ruled"), ("queen of ", "ruled"),
            ("emperor of ", "ruled"),
        ):
            idx = occupation.lower().find(predicate_label)
            if idx >= 0:
                obj_tail = occupation[idx + len(predicate_label):]
                obj = obj_tail.split(",")[0].strip().rstrip(".")
                m = _WIKILINK_RE.match(obj)
                if m:
                    obj = _extract_wikilink_target(m.group(0))
                if obj and obj != entity_name:
                    out.append(ProposedRelation(
                        id="",
                        predicate=canonical,
                        object=obj,
                        confidence="medium",
                        status="needs-refinement",
                        evidence_source=["metadata"],
                        evidence_excerpts=[EvidenceExcerpt(
                            location="metadata.occupation",
                            text=occupation,
                        )],
                        object_status="canonical_entity_exists",
                    ))

    return out


def _enrich_with_crossref(
    entity_name: str,
    proposals: list[ProposedRelation],
    db_path: Path,
) -> list[ProposedRelation]:
    """For each proposed (predicate, object), check if the inverse typed edge
    already exists in SQLite with this entity as target. If so, append a
    `cross-ref` source to the evidence (never auto-generates an edge).
    """
    if not db_path.exists() or not proposals:
        return proposals

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        for p in proposals:
            cur.execute(
                "SELECT source_entity, predicate FROM entity_relations "
                "WHERE target_entity = ? AND source_entity = ? "
                "AND predicate IS NOT NULL LIMIT 1",
                (entity_name, p.object),
            )
            row = cur.fetchone()
            if row is None:
                continue
            # Cross-ref evidence: the other note already typed this edge
            # pointing back at us. We flag it but do NOT invert anything.
            source_ent, other_pred = row
            if "cross-ref" not in p.evidence_source:
                p.evidence_source.append("cross-ref")
            p.evidence_excerpts.append(EvidenceExcerpt(
                location=f"cross-ref.{source_ent}",
                text=f"{source_ent} has typed `{other_pred} -> {entity_name}`",
            ))
    finally:
        conn.close()
    return proposals


# ---------------------------------------------------------------------------
# Object-status resolution
# ---------------------------------------------------------------------------


def _build_entity_index(vault: Vault) -> dict[str, str]:
    """Map canonical entity name -> object_kind (entity|disambiguation_page|...)."""
    index: dict[str, str] = {}
    for path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
        try:
            text = path.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(text)
        except Exception:
            continue
        name = fm.get("name")
        if not isinstance(name, str):
            continue
        if fm.get("object_kind") == "disambiguation_page":
            index[name] = "disambiguation_page"
        elif fm.get("entity") is True:
            index[name] = "entity"
    return index


def _resolve_object_status(obj: str, index: dict[str, str]) -> ObjectStatus:
    kind = index.get(obj)
    if kind == "entity":
        return "canonical_entity_exists"
    if kind == "disambiguation_page":
        return "DISAMBIGUATION_PAGE"
    return "MISSING_ENTITY"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _find_note_for_entity(entity_name: str, vault: Vault) -> Path:
    for path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
        if path.stem == entity_name:
            return path
    raise FileNotFoundError(f"No note found for entity: {entity_name}")


def _collect_existing_typed(frontmatter: dict) -> set[tuple[str, str]]:
    parse_result = parse_relationships(frontmatter.get("name", ""), frontmatter)
    return {(r.predicate, r.object) for r in parse_result.typed}


def _id_prefix(entity_name: str) -> str:
    """2-char lowercase prefix from entity name (accents stripped)."""
    import unicodedata
    normalized = unicodedata.normalize("NFD", entity_name)
    letters = [c.lower() for c in normalized if c.isalpha() and not unicodedata.combining(c)]
    if len(letters) >= 2:
        return letters[0] + letters[1]
    return (letters[0] if letters else "x") + "x"


def propose_relations_for_entity(
    entity_name: str,
    vault: Vault,
    *,
    db_path: Path | None = None,
    include_existing: bool = False,
) -> ProposalResult:
    """Produce a ProposalResult for one entity. Does not write the vault."""

    note_path = _find_note_for_entity(entity_name, vault)
    text = note_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)

    existing_typed = _collect_existing_typed(frontmatter)
    related = frontmatter.get("related") or []
    if not isinstance(related, list):
        related = []

    body_candidates = _extract_from_body(entity_name, body)
    metadata_candidates = _extract_from_metadata(entity_name, frontmatter)

    merged: dict[tuple[str, str], ProposedRelation] = {}
    for cand in body_candidates + metadata_candidates:
        key = (cand.predicate, cand.object)
        existing = merged.get(key)
        if existing is None:
            merged[key] = cand
        else:
            # Union evidence sources + excerpts; keep highest confidence.
            for src in cand.evidence_source:
                if src not in existing.evidence_source:
                    existing.evidence_source.append(src)
            existing.evidence_excerpts.extend(cand.evidence_excerpts)
            if cand.confidence == "high":
                existing.confidence = "high"
                existing.status = "approved"

    # Boost evidence for items also present in related (never creates proposals).
    related_names = {r if isinstance(r, str) else str(r) for r in related}
    for key, p in merged.items():
        if p.object in related_names and "related" not in p.evidence_source:
            p.evidence_source.append("related")
            p.evidence_excerpts.append(EvidenceExcerpt(
                location="related",
                text=f"`{p.object}` present in legacy `related:` list",
            ))

    # Filter already-typed unless user asked to include.
    if not include_existing:
        merged = {k: v for k, v in merged.items() if k not in existing_typed}

    proposals = list(merged.values())

    # Resolve object_status for each proposal.
    entity_index = _build_entity_index(vault)
    for p in proposals:
        p.object_status = _resolve_object_status(p.object, entity_index)
        if p.object_status == "MISSING_ENTITY":
            p.note = (
                "Objeto no existe como entidad canónica. El triple se emite "
                "pero `brain apply-relations-batch` no lo aplicará salvo que "
                "se pase `--allow-mentions`."
            )
        elif p.object_status == "DISAMBIGUATION_PAGE":
            p.note = (
                "Objeto apunta a una disambiguation_page. Refinar a la "
                "variante específica antes de aplicar."
            )

    # Enrich with cross-ref evidence (SQLite).
    if db_path is not None:
        proposals = _enrich_with_crossref(entity_name, proposals, db_path)

    # Sort: high before medium, then predicate, then object.
    def _sort_key(p: ProposedRelation) -> tuple:
        return (0 if p.confidence == "high" else 1, p.predicate, p.object)

    proposals.sort(key=_sort_key)

    # Assign stable IDs now that order is fixed.
    prefix = _id_prefix(entity_name)
    for idx, p in enumerate(proposals, start=1):
        p.id = f"{prefix}-{idx:02d}"

    missing = sorted({p.object for p in proposals if p.object_status == "MISSING_ENTITY"})

    subtype = frontmatter.get("subtype")
    domain = frontmatter.get("domain")

    notes = (
        "Extracción pattern-based (sin LLM). Revisa cada triple y cambia "
        "`status` a `approved` o `rejected`. Medium-confidence arranca "
        "como `needs-refinement` — debe ser aprobado manualmente antes "
        "del apply."
    )

    return ProposalResult(
        entity=entity_name,
        subtype=subtype if isinstance(subtype, str) else None,
        domain=domain,
        baseline=ProposalBaseline(
            typed=len(existing_typed),
            legacy_related=len(related),
            body_chars=len(body),
        ),
        proposal=proposals,
        missing_entities_if_approved=missing,
        notes_from_proposer=notes,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        batch=None,
    )


__all__ = [
    "EVIDENCE_SOURCES",
    "EvidenceExcerpt",
    "ObjectStatus",
    "ProposedRelation",
    "ProposalBaseline",
    "ProposalResult",
    "propose_relations_for_entity",
]
