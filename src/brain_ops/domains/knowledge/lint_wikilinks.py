"""Wikilink integrity linter for Knowledge notes.

Detects three classes of issue in `.md` bodies:

1. **nested** — corrupt nested-bracket syntax `[[X ([[Y]])|alias]]` or
   `[[X ([[Y]])]]`. Produced by past automated wikify scripts that
   mis-handled disambiguation. Auto-fixable mechanically (collapse
   the inner brackets).

2. **broken** — wikilink whose target file does not exist in the vault.
   Cannot be auto-fixed safely.

3. **ambiguous_bare** — bare-name link `[[Foo]]` where `Foo.md` does
   NOT exist but one or more disambiguated forms `Foo (X).md` do.
   Reader has no way to know which disambiguation was intended.

Read-only API. The CLI exposes `--fix-nested` for the safe mechanical
fix; broken and ambiguous_bare always require human judgment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# Nested corruption: [[X ([[Y]])|alias]] or [[X ([[Y]])]]
# More specific than the generic wikilink pattern; matched first so the
# generic pass can ignore them.
NESTED_RE = re.compile(
    r"\[\[([^\[\]|]+) \(\[\[([^\[\]|]+)\]\]\)(?:\|([^\[\]]+))?\]\]"
)

# Generic wikilink: [[Target]] or [[Target|alias]]. Excludes nested.
WIKILINK_RE = re.compile(
    r"\[\[([^\[\]|]+?)(?:\|([^\[\]]+))?\]\]"
)

# A canonical name that ends with " (Disambiguator)" — e.g.
# "Meditaciones (Marco Aurelio)".
DISAMBIGUATED_RE = re.compile(r"^(.+?)\s+\(([^()]+)\)$")


@dataclass(slots=True, frozen=True)
class LintIssue:
    file: str
    line: int
    column: int
    rule: str
    snippet: str
    target: str
    suggestion: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "rule": self.rule,
            "snippet": self.snippet,
            "target": self.target,
            "suggestion": self.suggestion,
        }


@dataclass(slots=True)
class LintReport:
    files_scanned: int = 0
    links_scanned: int = 0
    issues: list[LintIssue] = field(default_factory=list)

    def by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for i in self.issues:
            counts[i.rule] = counts.get(i.rule, 0) + 1
        return counts

    def to_dict(self) -> dict[str, object]:
        return {
            "files_scanned": self.files_scanned,
            "links_scanned": self.links_scanned,
            "issue_count": len(self.issues),
            "by_rule": self.by_rule(),
            "issues": [i.to_dict() for i in self.issues],
        }


def build_vault_index(
    knowledge_dir: Path,
) -> tuple[set[str], dict[str, list[str]]]:
    """Return (canonical_names, bare_to_disambig).

    canonical_names: every `<stem>` for `<stem>.md` directly under
    `knowledge_dir` (no recursion — disambig pages live alongside).

    bare_to_disambig: maps a bare prefix to the list of disambiguated
    forms that exist. E.g.
        {"Meditaciones": ["Meditaciones (Marco Aurelio)",
                          "Meditaciones metafísicas"]}
    """
    canonical: set[str] = set()
    bare_to_disambig: dict[str, list[str]] = {}
    for md in knowledge_dir.glob("*.md"):
        stem = md.stem
        canonical.add(stem)
        m = DISAMBIGUATED_RE.match(stem)
        if m:
            bare = m.group(1)
            bare_to_disambig.setdefault(bare, []).append(stem)
    return canonical, bare_to_disambig


def lint_text(
    text: str,
    relative_path: str,
    canonical_names: set[str],
    bare_to_disambig: dict[str, list[str]],
) -> tuple[int, list[LintIssue]]:
    """Lint a single note body. Pure function — no I/O.

    Returns (links_scanned, issues).
    """
    issues: list[LintIssue] = []
    links_scanned = 0

    # Pass 1: nested corruption (line-by-line for accurate line numbers).
    for line_num, line in enumerate(text.splitlines(), start=1):
        for m in NESTED_RE.finditer(line):
            outer, inner, alias = m.group(1), m.group(2), m.group(3)
            if alias:
                suggestion = f"[[{outer} ({inner})|{alias}]]"
            else:
                suggestion = f"[[{outer} ({inner})]]"
            issues.append(LintIssue(
                file=relative_path,
                line=line_num,
                column=m.start() + 1,
                rule="nested",
                snippet=m.group(0),
                target=f"{outer} ({inner})",
                suggestion=suggestion,
            ))
            links_scanned += 1

    # Pass 2: broken / ambiguous_bare — strip nested matches first to
    # avoid double-counting.
    text_clean = NESTED_RE.sub("__NESTED__", text)
    for line_num, line in enumerate(text_clean.splitlines(), start=1):
        for m in WIKILINK_RE.finditer(line):
            target_raw = m.group(1).strip()
            # Strip section anchors `Foo#Section`
            if "#" in target_raw:
                target_raw = target_raw.split("#", 1)[0].strip()
                if not target_raw:
                    continue
            links_scanned += 1
            if target_raw in canonical_names:
                continue
            if target_raw in bare_to_disambig:
                disambigs = bare_to_disambig[target_raw]
                issues.append(LintIssue(
                    file=relative_path,
                    line=line_num,
                    column=m.start() + 1,
                    rule="ambiguous_bare",
                    snippet=m.group(0),
                    target=target_raw,
                    suggestion=f"choose one of: {', '.join(disambigs)}",
                ))
            else:
                issues.append(LintIssue(
                    file=relative_path,
                    line=line_num,
                    column=m.start() + 1,
                    rule="broken",
                    snippet=m.group(0),
                    target=target_raw,
                    suggestion=None,
                ))

    return links_scanned, issues


def lint_vault(
    vault_path: Path,
    *,
    only_rule: str | None = None,
) -> LintReport:
    """Scan every `.md` under `<vault>/02 - Knowledge/`. Read-only."""
    knowledge_dir = vault_path / "02 - Knowledge"
    if not knowledge_dir.exists():
        return LintReport()
    canonical, bare_to_disambig = build_vault_index(knowledge_dir)
    report = LintReport()
    for md in sorted(knowledge_dir.rglob("*.md")):
        rel = str(md.relative_to(vault_path))
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        report.files_scanned += 1
        n_links, file_issues = lint_text(text, rel, canonical, bare_to_disambig)
        report.links_scanned += n_links
        if only_rule:
            file_issues = [i for i in file_issues if i.rule == only_rule]
        report.issues.extend(file_issues)
    return report


def _collapse_nested(m: re.Match[str]) -> str:
    outer, inner, alias = m.group(1), m.group(2), m.group(3)
    if alias:
        return f"[[{outer} ({inner})|{alias}]]"
    return f"[[{outer} ({inner})]]"


def fix_nested_in_text(text: str) -> tuple[str, int]:
    """Pure helper — collapse all nested-bracket wikilinks in one string.

    Returns (new_text, count_fixed).
    """
    return NESTED_RE.subn(_collapse_nested, text)


def fix_nested_wikilinks(vault_path: Path) -> tuple[int, int]:
    """Apply the safe mechanical fix vault-wide.

    Returns (files_changed, links_fixed). Body bytes outside the
    nested-link spans are preserved exactly.
    """
    knowledge_dir = vault_path / "02 - Knowledge"
    if not knowledge_dir.exists():
        return 0, 0
    files_changed = 0
    links_fixed = 0
    for md in knowledge_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        new_text, count = fix_nested_in_text(text)
        if count > 0:
            md.write_text(new_text, encoding="utf-8")
            files_changed += 1
            links_fixed += count
    return files_changed, links_fixed


__all__ = [
    "LintIssue",
    "LintReport",
    "build_vault_index",
    "fix_nested_in_text",
    "fix_nested_wikilinks",
    "lint_text",
    "lint_vault",
]
