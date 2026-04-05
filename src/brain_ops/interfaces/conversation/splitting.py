from __future__ import annotations

import re

ACTION_STARTERS = [
    "pagué",
    "pague",
    "gasté",
    "gaste",
    "compré",
    "compre",
    "tomé",
    "tome",
    "aprendí",
    "aprendi",
    "hice",
    "pesé",
    "pese",
    "medí",
    "medi",
    "desayuné",
    "desayune",
    "comí",
    "comi",
    "cené",
    "cene",
    "almorcé",
    "almorce",
    "leí",
    "lei",
]

ACTION_CONNECTOR_PATTERN = re.compile(
    r"\s+(?:y|tamb[ié]n|adem[aá]s)\s+(?=(?:hoy\s+|me\s+)?(?:"
    + "|".join(re.escape(starter) for starter in ACTION_STARTERS)
    + r")\b)",
    re.IGNORECASE,
)
COMPOUND_SPLIT_PATTERN = re.compile(
    r"\s*(?:[.;]\s+|\s+y luego\s+|\s+despu[eé]s\s+|\s+adem[aá]s\s+)\s*",
    re.IGNORECASE,
)


def split_compound_input(text: str) -> list[str]:
    normalized = ACTION_CONNECTOR_PATTERN.sub(" ; ", text.strip())
    clauses = [
        part.strip(" ,")
        for part in COMPOUND_SPLIT_PATTERN.split(normalized)
        if part.strip(" ,")
    ]
    return clauses if len(clauses) > 1 else [text.strip()]
