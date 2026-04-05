from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from brain_ops.storage.sqlite import delete_follow_up, fetch_follow_up_payload, upsert_follow_up


class PendingFollowUp(BaseModel):
    followup_type: str
    question: str
    options: list[str] = Field(default_factory=list)
    default_option: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


def save_follow_up(database_path: Path, session_id: str, pending: PendingFollowUp) -> None:
    upsert_follow_up(
        database_path,
        session_id=session_id,
        followup_type=pending.followup_type,
        payload_json=pending.model_dump_json(),
        updated_at=datetime.now().isoformat(timespec="seconds"),
    )


def load_follow_up(database_path: Path, session_id: str) -> PendingFollowUp | None:
    payload_json = fetch_follow_up_payload(database_path, session_id=session_id)
    if payload_json is None:
        return None
    return PendingFollowUp.model_validate(json.loads(payload_json))


def clear_follow_up(database_path: Path, session_id: str) -> None:
    delete_follow_up(database_path, session_id=session_id)


def active_diet_pending_follow_up(diet_name: str) -> PendingFollowUp:
    return PendingFollowUp(
        followup_type="active_diet_options",
        question=f"Tu dieta activa es {diet_name}. ¿Quieres resumen, objetivos o recomendaciones?",
        options=["resumen", "objetivos", "recomendaciones"],
        default_option="resumen",
        context={"diet_name": diet_name},
    )
