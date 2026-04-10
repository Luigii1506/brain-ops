from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProjectScaffoldNotePlan:
    title: str
    note_type: str
    extra_frontmatter: dict[str, object]
    folder_suffix: str | None = None


def plan_project_scaffold(
    project_name: str,
    scaffold_files: tuple[tuple[str, str], ...] | tuple[tuple[str, str | None, str, str], ...],
) -> list[ProjectScaffoldNotePlan]:
    """Plan scaffold notes for a project.

    Accepts either legacy 2-tuple format (note_type, title_template)
    or layered 4-tuple format (layer, subfolder, note_type, title_template).
    """
    plans: list[ProjectScaffoldNotePlan] = []
    for entry in scaffold_files:
        if len(entry) == 2:
            note_type, title_template = entry
            folder_suffix = None
        else:
            layer, subfolder, note_type, title_template = entry
            folder_suffix = f"{layer}/{subfolder}" if subfolder else layer
        plans.append(
            ProjectScaffoldNotePlan(
                title=title_template.format(title=project_name),
                note_type=note_type,
                extra_frontmatter={"project": project_name},
                folder_suffix=folder_suffix,
            )
        )
    return plans


def plan_scaffold_directories(dirs: tuple[str, ...]) -> list[str]:
    """Return list of subdirectory paths to create for a layered project."""
    return list(dirs)
