"""Semantic relationship suggestions for knowledge entities.

This complements cross-enrichment: cross-enrichment closes explicit wikilink gaps;
semantic relations suggests likely graph edges and missing entities from context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter


@dataclass(slots=True, frozen=True)
class SemanticRelationSuggestion:
    name: str
    predicate: str
    reason: str
    confidence: float
    exists: bool
    action: str


_STOP_CANDIDATES = {
    "Identity",
    "Key Facts",
    "Narrative",
    "Characters",
    "Themes",
    "Symbolism",
    "Cultural Impact",
    "Versions",
    "Sources",
    "Relationships",
    "Related notes",
    "Preguntas",
    "Grecia",
    "También",
    "Regreso",
    "Porque",
    "Para",
    "Objetivo",
    "Líder",
    "Destino",
    "Diosas",
    "Consecuencia",
    "Barco",
    "Ayuda",
    "En",
}

_BROAD_EXISTING_NAMES = {"Amor", "Grecia"}
_CONNECTORS = {"y", "de", "del", "la", "el", "los", "las"}


def _wikilinks(text: str) -> set[str]:
    return {m.strip() for m in re.findall(r"\[\[([^\]|]+)", text)}


def _name_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\wÁÉÍÓÚÜÑáéíóúüñ]){re.escape(name)}(?![\wÁÉÍÓÚÜÑáéíóúüñ])", re.IGNORECASE)


def _contains_plain_name(body: str, name: str) -> bool:
    return bool(_name_pattern(name).search(body))


def _aliases_for(name: str, frontmatter: dict[str, Any]) -> set[str]:
    aliases: set[str] = set()
    raw_aliases = frontmatter.get("aliases")
    if isinstance(raw_aliases, list):
        aliases.update(str(a) for a in raw_aliases if isinstance(a, str) and len(a) >= 3)

    # Useful myth/history shorthand: [[Guerra de Troya]] is often mentioned as "Troya".
    if name.startswith("Guerra de "):
        tail = name.rsplit(" de ", 1)[-1].strip()
        if len(tail) >= 5:
            aliases.add(tail)

    return aliases


def _extract_related(frontmatter: dict[str, Any], body: str) -> set[str]:
    related: set[str] = set()
    raw_related = frontmatter.get("related")
    if isinstance(raw_related, list):
        related.update(str(r) for r in raw_related if isinstance(r, str))

    in_related = False
    for line in body.splitlines():
        if line.strip() == "## Related notes":
            in_related = True
            continue
        if in_related and line.startswith("## "):
            break
        if in_related:
            related.update(_wikilinks(line))

    return related


def _extract_section_links(body: str, section_name: str) -> set[str]:
    links: set[str] = set()
    in_section = False
    for line in body.splitlines():
        if line.strip() == f"## {section_name}":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            links.update(_wikilinks(line))
    return links


def _strip_sections(body: str, section_names: set[str]) -> str:
    kept: list[str] = []
    skip = False
    for line in body.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            skip = heading in section_names
            if skip:
                continue
        if not skip:
            kept.append(line)
    return "\n".join(kept)


def _semantic_boost(name: str, body_lower: str, current_related: set[str]) -> tuple[float, str] | None:
    if name == "Hécate" and "Medea" in current_related and any(k in body_lower for k in ["magia", "hechicer", "fármaco"]):
        return 0.82, "Medea is central and the note discusses magic/hechicera context"
    if name == "Helios" and "Medea" in current_related:
        return 0.72, "Medea is central and her solar lineage is graph-relevant"
    if name == "Eros" and "Medea" in current_related and any(k in body_lower for k in ["enamor", "deseo", "amor"]):
        return 0.78, "Medea's desire/enamoramiento is a causal force in the myth"
    if name == "Guerra de Troya" and any(k in body_lower for k in ["troya", "troyano"]):
        return 0.70, "the note situates the myth relative to Troy/Troya"
    return None


def _extract_missing_candidates(body: str, existing_names: set[str], current_name: str) -> list[SemanticRelationSuggestion]:
    candidates: dict[str, int] = {}
    existing_aliases = {alias for existing in existing_names for alias in _aliases_for(existing, {})}
    current_parts = {p for p in re.split(r"\s+y\s+|\s+", current_name) if len(p) >= 4}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("## ") or line.startswith("- [["):
            continue
        for match in re.finditer(
            r"\b[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+(?:y|de|del|la|el|los|las|[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)){0,4}",
            line,
        ):
            name = match.group(0).strip(" .,:;()")
            parts = name.split()
            while parts and parts[-1].lower() in _CONNECTORS:
                parts.pop()
            name = " ".join(parts)
            if len(name) < 4 or name in _STOP_CANDIDATES:
                continue
            if name.split()[0] in _STOP_CANDIDATES:
                continue
            if name.startswith(("En ", "El ", "La ", "Los ", "Las ")):
                continue
            if name == current_name or name in existing_names:
                continue
            if name in existing_aliases or name in current_parts or any(part in name.split() for part in current_parts):
                continue
            if any(name.startswith(prefix) for prefix in ["El ", "La ", "Los ", "Las "]):
                continue
            candidates[name] = candidates.get(name, 0) + 1

    # Drop shorter candidates that are contained in a stronger multi-word candidate.
    for name in list(candidates):
        if any(name != other and name in other and candidates[other] >= candidates[name] for other in candidates):
            candidates.pop(name, None)

    suggestions: list[SemanticRelationSuggestion] = []
    for name, count in candidates.items():
        confidence = 0.62 if count >= 2 else 0.55
        suggestions.append(SemanticRelationSuggestion(
            name=name,
            predicate="candidate_entity",
            reason="capitalized domain term appears in the note but has no entity note",
            confidence=confidence,
            exists=False,
            action="create",
        ))
    return suggestions


def suggest_semantic_relations(
    current_name: str,
    current_text: str,
    entity_notes: dict[str, tuple[Path, dict[str, Any], str]],
) -> list[SemanticRelationSuggestion]:
    current_fm, current_body = split_frontmatter(current_text)
    existing_names = set(entity_notes)
    related = _extract_related(current_fm, current_body)
    relationship_links = _extract_section_links(current_body, "Relationships")
    analysis_body = _strip_sections(current_body, {"Related notes"})
    links = _wikilinks(analysis_body)
    body_lower = analysis_body.lower()

    suggestions: dict[tuple[str, str], SemanticRelationSuggestion] = {}

    def add(s: SemanticRelationSuggestion) -> None:
        key = (s.name, s.action)
        existing = suggestions.get(key)
        if existing is None or s.confidence > existing.confidence:
            suggestions[key] = s

    for name, (_path, fm, _body) in entity_notes.items():
        if name == current_name or name in relationship_links:
            continue
        if name not in _BROAD_EXISTING_NAMES and len(name) >= 5 and _contains_plain_name(analysis_body, name):
            add(SemanticRelationSuggestion(name, "related_to", "entity name appears as plain text but is not linked/related", 0.90, True, "link"))
            continue
        for alias in _aliases_for(name, fm):
            if _contains_plain_name(analysis_body, alias):
                add(SemanticRelationSuggestion(name, "related_to", f"alias/plain context '{alias}' appears in the note", 0.68, True, "link"))
                break

        boosted = _semantic_boost(name, body_lower, related | links)
        if boosted:
            confidence, reason = boosted
            add(SemanticRelationSuggestion(name, "related_to", reason, confidence, True, "link"))

    for s in _extract_missing_candidates(analysis_body, existing_names, current_name):
        if s.name not in related and s.name not in links:
            add(s)

    return sorted(suggestions.values(), key=lambda s: (s.exists, s.confidence, s.name), reverse=True)


def add_semantic_related_links(text: str, suggestions: list[SemanticRelationSuggestion], *, min_confidence: float = 0.7) -> tuple[str, list[SemanticRelationSuggestion]]:
    frontmatter, body = split_frontmatter(text)
    related = _extract_related(frontmatter, body)
    relationship_links = _extract_section_links(body, "Relationships")
    applied = [
        s for s in suggestions
        if s.exists
        and s.action == "link"
        and s.confidence >= min_confidence
        and (s.name not in related or s.name not in relationship_links)
    ]
    if not applied:
        return text, []

    raw_related = frontmatter.get("related")
    if not isinstance(raw_related, list):
        raw_related = []
    merged = [str(r) for r in raw_related if isinstance(r, str)]
    for suggestion in applied:
        if suggestion.name not in merged:
            merged.append(suggestion.name)
    frontmatter["related"] = merged

    lines = body.splitlines()
    relationship_insert_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Relationships":
            j = idx + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            relationship_insert_idx = j
            break
    if relationship_insert_idx is None:
        lines.extend(["", "## Relationships"])
        relationship_insert_idx = len(lines)

    relationship_new_lines = [
        f"- [[{s.name}]] — {s.predicate} — {s.reason} *(semantic)*"
        for s in applied
        if s.name not in relationship_links
    ]
    lines = lines[:relationship_insert_idx] + relationship_new_lines + lines[relationship_insert_idx:]

    insert_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Related notes":
            j = idx + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            insert_idx = j
            break
    if insert_idx is None:
        lines.extend(["", "## Related notes"])
        insert_idx = len(lines)

    new_lines = [f"- [[{s.name}]]" for s in applied if s.name not in related]
    body = "\n".join(lines[:insert_idx] + new_lines + lines[insert_idx:])
    return dump_frontmatter(frontmatter, body), applied


def build_reciprocal_semantic_suggestion(source_name: str, suggestion: SemanticRelationSuggestion) -> SemanticRelationSuggestion:
    return SemanticRelationSuggestion(
        name=source_name,
        predicate=suggestion.predicate,
        reason=f"relación recíproca inferida desde [[{source_name}]]: {suggestion.reason}",
        confidence=suggestion.confidence,
        exists=True,
        action="link",
    )


__all__ = [
    "SemanticRelationSuggestion",
    "add_semantic_related_links",
    "build_reciprocal_semantic_suggestion",
    "suggest_semantic_relations",
]
