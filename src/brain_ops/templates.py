from __future__ import annotations

from pathlib import Path

from brain_ops.errors import ConfigError


def render_template(template_path: Path, context: dict[str, object]) -> str:
    if not template_path.exists():
        raise ConfigError(f"Template not found: {template_path}")

    rendered = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def resolve_template_path(template_dir: Path, template_name: str) -> Path:
    candidate = Path(template_name)
    if candidate.suffix != ".md":
        candidate = candidate.with_suffix(".md")

    if candidate.is_absolute():
        return candidate

    return template_dir / candidate
