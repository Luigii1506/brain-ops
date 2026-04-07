"""Source strategy — adapt extraction behavior to source type."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


SOURCE_TYPES = (
    "encyclopedia", "article", "news", "research_paper",
    "documentation", "tutorial", "thread", "notes",
)


@dataclass(slots=True, frozen=True)
class SourceStrategy:
    source_type: str
    chunk_priority_keywords: list[str]
    extraction_focus: str
    entity_bias: str  # "high" = likely to produce entities, "low" = mostly insights
    event_bias: str   # "high" = likely an event, "low" = atemporal knowledge
    max_context_chars: int = 8000
    extra_instructions: str = ""


STRATEGIES: dict[str, SourceStrategy] = {
    "encyclopedia": SourceStrategy(
        source_type="encyclopedia",
        chunk_priority_keywords=[
            "biografía", "biography", "historia", "history", "introducción", "introduction",
            "legado", "legacy", "muerte", "death", "nacimiento", "birth", "carrera", "career",
            "campañas", "campaigns", "obras", "works", "geografía", "geography",
        ],
        extraction_focus="Extract complete identity, canonical facts, full timeline, and explicit relationships. This is a reference source — prioritize breadth and accuracy.",
        entity_bias="high",
        event_bias="low",
        max_context_chars=8000,
    ),
    "article": SourceStrategy(
        source_type="article",
        chunk_priority_keywords=[
            "conclusion", "conclusión", "key", "clave", "insight", "argument", "argumento",
            "example", "ejemplo", "opinion", "analysis", "análisis", "takeaway",
        ],
        extraction_focus="Extract the author's main ideas, arguments, and insights. Focus on what's novel or non-obvious. Don't just summarize — capture the signal.",
        entity_bias="medium",
        event_bias="low",
        max_context_chars=6000,
    ),
    "news": SourceStrategy(
        source_type="news",
        chunk_priority_keywords=[
            "headline", "titular", "breaking", "reported", "announced", "anunció",
            "impact", "impacto", "consequence", "response", "respuesta",
        ],
        extraction_focus="Extract the core event: WHO did WHAT, WHEN, WHERE, and WHY it matters. Focus on the immediate event and its impact. Keep it factual and time-bound.",
        entity_bias="medium",
        event_bias="high",
        max_context_chars=4000,
        extra_instructions="If this describes a specific event, extract it as a timeline entry with a clear date. Identify the main actors and their roles.",
    ),
    "research_paper": SourceStrategy(
        source_type="research_paper",
        chunk_priority_keywords=[
            "abstract", "resumen", "introduction", "introducción", "results", "resultados",
            "conclusion", "conclusión", "methodology", "metodología", "findings", "hallazgos",
            "contribution", "contribución", "discussion", "discusión",
        ],
        extraction_focus="Extract the research problem, methodology, key findings, and contribution. What question does it answer? What did they discover? What are the limitations?",
        entity_bias="low",
        event_bias="low",
        max_context_chars=8000,
        extra_instructions="Prioritize: Abstract > Results > Conclusion > Methodology. Capture the core contribution in one sentence.",
    ),
    "documentation": SourceStrategy(
        source_type="documentation",
        chunk_priority_keywords=[
            "getting started", "installation", "setup", "configuración", "usage", "uso",
            "api", "reference", "referencia", "concepts", "conceptos", "architecture",
            "overview", "quick start",
        ],
        extraction_focus="Extract what the tool/library IS, what it's FOR, key concepts, and how to use it. Focus on understanding over procedure.",
        entity_bias="medium",
        event_bias="low",
        max_context_chars=6000,
    ),
    "tutorial": SourceStrategy(
        source_type="tutorial",
        chunk_priority_keywords=[
            "step", "paso", "prerequisite", "requisito", "goal", "objetivo",
            "result", "resultado", "warning", "tip", "note", "example",
        ],
        extraction_focus="Extract the learning objective, key steps, tools used, and common pitfalls. What does someone learn from this?",
        entity_bias="low",
        event_bias="low",
        max_context_chars=5000,
    ),
    "thread": SourceStrategy(
        source_type="thread",
        chunk_priority_keywords=[
            "thread", "hilo", "1/", "key", "clave", "takeaway", "insight",
            "hot take", "unpopular", "important", "importante",
        ],
        extraction_focus="Extract the main claims and takeaways. Threads are fragmented — synthesize the core argument. Identify who said it if relevant.",
        entity_bias="low",
        event_bias="low",
        max_context_chars=4000,
        extra_instructions="Threads often contain opinions, not facts. Mark claims as opinions where appropriate.",
    ),
    "notes": SourceStrategy(
        source_type="notes",
        chunk_priority_keywords=[
            "idea", "thought", "pensamiento", "note", "nota", "todo", "question",
            "pregunta", "learned", "aprendí", "reflection", "reflexión",
        ],
        extraction_focus="Extract the core ideas, questions, and reflections. These are personal notes — capture what the author found important or surprising.",
        entity_bias="low",
        event_bias="low",
        max_context_chars=4000,
        extra_instructions="Personal notes may contain subjective observations. Preserve the personal perspective — this is part of the knowledge system's memory.",
    ),
}


# Domain-based classification hints
DOMAIN_HINTS: dict[str, str] = {
    "wikipedia.org": "encyclopedia",
    "britannica.com": "encyclopedia",
    "youtube.com": "tutorial",
    "youtu.be": "tutorial",
    "arxiv.org": "research_paper",
    "scholar.google": "research_paper",
    "medium.com": "article",
    "substack.com": "article",
    "dev.to": "article",
    "github.com": "documentation",
    "docs.python.org": "documentation",
    "react.dev": "documentation",
    "nextjs.org": "documentation",
    "twitter.com": "thread",
    "x.com": "thread",
    "reddit.com": "thread",
    "news.ycombinator.com": "news",
    "bbc.com": "news",
    "cnn.com": "news",
    "reuters.com": "news",
    "elpais.com": "news",
}

# Text heuristics for classification
TEXT_HEURISTICS: list[tuple[list[str], str]] = [
    (["abstract", "methodology", "findings", "hypothesis"], "research_paper"),
    (["step 1", "step 2", "prerequisites", "tutorial"], "tutorial"),
    (["1/", "thread", "hilo", "🧵"], "thread"),
    (["breaking", "reported", "announced", "según fuentes"], "news"),
    (["getting started", "installation", "npm install", "pip install", "api reference"], "documentation"),
    (["chapter", "capítulo", "libro", "book"], "article"),
]


def classify_source(url: str | None, text: str) -> str:
    """Classify a source into a source type."""
    # 1. Check domain hints
    if url:
        domain = urlparse(url).netloc.lower()
        for hint_domain, hint_type in DOMAIN_HINTS.items():
            if hint_domain in domain:
                return hint_type

    # 2. Check text heuristics
    lowered = text[:1000].lower()
    for keywords, source_type in TEXT_HEURISTICS:
        matches = sum(1 for kw in keywords if kw in lowered)
        if matches >= 2:
            return source_type

    # 3. Default
    return "article"


def strategy_for_source(source_type: str) -> SourceStrategy:
    """Get the extraction strategy for a source type."""
    return STRATEGIES.get(source_type, STRATEGIES["article"])


SOURCE_TYPE_PROMPTS: dict[str, str] = {
    "encyclopedia": """You are extracting knowledge from an ENCYCLOPEDIA article.
Focus on: complete identity, canonical facts, full timeline, relationships, and lasting impact.
This is a reference source — be thorough and accurate.""",

    "article": """You are extracting knowledge from a BLOG POST or ARTICLE.
Focus on: the author's main ideas, novel insights, and key arguments.
Don't just summarize — capture what's original or thought-provoking.""",

    "news": """You are extracting knowledge from a NEWS article.
Focus on: the core event (WHO, WHAT, WHEN, WHERE, WHY).
Capture the immediate event and its significance. Be factual and time-specific.""",

    "research_paper": """You are extracting knowledge from a RESEARCH PAPER.
Focus on: the problem, methodology, key findings, and contribution.
What question was answered? What was discovered? What are the limitations?""",

    "documentation": """You are extracting knowledge from TECHNICAL DOCUMENTATION.
Focus on: what the tool/library IS, what it's FOR, key concepts, and architecture.
Prioritize understanding over procedural details.""",

    "tutorial": """You are extracting knowledge from a TUTORIAL.
Focus on: the learning objective, key steps, tools used, and common pitfalls.
What does someone learn from this? What's the practical takeaway?""",

    "thread": """You are extracting knowledge from a SOCIAL MEDIA THREAD.
Focus on: the main claims, takeaways, and any novel arguments.
Threads are fragmented — synthesize the core message. Flag opinions vs facts.""",

    "notes": """You are extracting knowledge from PERSONAL NOTES.
Focus on: core ideas, questions, reflections, and personal observations.
Preserve the subjective perspective — this is part of the user's knowledge memory.""",
}


def get_source_type_prompt(source_type: str) -> str:
    """Get the type-specific instruction block for a source type."""
    return SOURCE_TYPE_PROMPTS.get(source_type, SOURCE_TYPE_PROMPTS["article"])


__all__ = [
    "DOMAIN_HINTS",
    "SOURCE_TYPES",
    "SOURCE_TYPE_PROMPTS",
    "STRATEGIES",
    "SourceStrategy",
    "classify_source",
    "get_source_type_prompt",
    "strategy_for_source",
]
