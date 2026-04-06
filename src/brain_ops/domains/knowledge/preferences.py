"""User preference profile for knowledge extraction tuning."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class UserPreferences:
    language: str = "spanish"
    detail_level: str = "high"
    preferred_sections: list[str] = field(default_factory=lambda: [
        "Identity", "Key Facts", "Timeline", "Impact",
        "Relationships", "Strategic Insights",
    ])
    interests: list[str] = field(default_factory=lambda: [
        "history", "science", "programming", "geography",
    ])
    style_notes: list[str] = field(default_factory=lambda: [
        "Prefer information-dense content over verbose explanations",
        "Always include explicit relationships with predicates",
        "Prefer specific dates and facts over vague descriptions",
        "Include strategic patterns and non-obvious lessons",
        "Flag contradictions and uncertainties explicitly",
    ])

    def to_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "detail_level": self.detail_level,
            "preferred_sections": list(self.preferred_sections),
            "interests": list(self.interests),
            "style_notes": list(self.style_notes),
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> UserPreferences:
        return UserPreferences(
            language=str(data.get("language", "spanish")),
            detail_level=str(data.get("detail_level", "high")),
            preferred_sections=list(data.get("preferred_sections", [])),
            interests=list(data.get("interests", [])),
            style_notes=list(data.get("style_notes", [])),
        )

    def to_prompt_context(self) -> str:
        lines = [
            f"User language preference: {self.language}",
            f"Detail level: {self.detail_level}",
            f"Interests: {', '.join(self.interests)}",
        ]
        if self.style_notes:
            lines.append("Style rules:")
            for note in self.style_notes:
                lines.append(f"- {note}")
        return "\n".join(lines)


def load_user_preferences(preferences_path: Path) -> UserPreferences:
    if not preferences_path.exists():
        return UserPreferences()
    data = json.loads(preferences_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return UserPreferences()
    return UserPreferences.from_dict(data)


def save_user_preferences(preferences_path: Path, preferences: UserPreferences) -> Path:
    preferences_path.parent.mkdir(parents=True, exist_ok=True)
    preferences_path.write_text(
        json.dumps(preferences.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return preferences_path


__all__ = [
    "UserPreferences",
    "load_user_preferences",
    "save_user_preferences",
]
