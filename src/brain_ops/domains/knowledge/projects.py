from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProjectScaffoldNotePlan:
    title: str
    note_type: str
    extra_frontmatter: dict[str, object]


def plan_project_scaffold(project_name: str, scaffold_files: tuple[tuple[str, str], ...]) -> list[ProjectScaffoldNotePlan]:
    return [
        ProjectScaffoldNotePlan(
            title=title_template.format(title=project_name),
            note_type=note_type,
            extra_frontmatter={"project": project_name},
        )
        for note_type, title_template in scaffold_files
    ]
