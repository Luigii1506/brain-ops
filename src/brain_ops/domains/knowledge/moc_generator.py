"""MOC (Map of Content) auto-generation from knowledge graph."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class GraphNode:
    name: str
    object_kind: str
    subtype: str
    source_count: int = 0
    degree: int = 0
    importance: float = 0.0


@dataclass(slots=True, frozen=True)
class GraphEdge:
    subject: str
    object: str
    predicate: str | None = None


@dataclass(slots=True, frozen=True)
class Cluster:
    name: str
    nodes: list[str]
    description: str


@dataclass(slots=True, frozen=True)
class Route:
    title: str
    path: list[str]
    narrative: str


@dataclass(slots=True, frozen=True)
class GeneratedMOC:
    topic: str
    description: str
    top_nodes: list[GraphNode]
    clusters: list[Cluster]
    key_relations: list[GraphEdge]
    routes: list[Route]
    questions: list[str]
    timeline_entries: list[tuple[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "topic": self.topic,
            "top_nodes": [n.name for n in self.top_nodes],
            "clusters": [{"name": c.name, "nodes": c.nodes} for c in self.clusters],
            "routes": [{"title": r.title, "path": r.path} for r in self.routes],
            "questions": list(self.questions),
        }


# ============================================================================
# GRAPH BUILDING
# ============================================================================

def build_graph_from_vault(
    notes: list[tuple[str, dict[str, object], str]],
) -> tuple[dict[str, GraphNode], list[GraphEdge]]:
    """Build a graph from vault notes with frontmatter."""
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    for _path, fm, _body in notes:
        if fm.get("entity") is not True:
            continue
        name = fm.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        node = GraphNode(
            name=name.strip(),
            object_kind=str(fm.get("object_kind", "entity")),
            subtype=str(fm.get("subtype", fm.get("type", ""))),
            source_count=1,
        )
        nodes[name.strip()] = node

        related = fm.get("related")
        if isinstance(related, list):
            for rel in related:
                if isinstance(rel, str) and rel.strip():
                    edges.append(GraphEdge(subject=name.strip(), object=rel.strip()))

    # Calculate degree
    for edge in edges:
        if edge.subject in nodes:
            nodes[edge.subject].degree += 1
        if edge.object in nodes:
            nodes[edge.object].degree += 1

    # Calculate importance
    for node in nodes.values():
        node.importance = (
            node.source_count * 0.2 +
            node.degree * 0.5 +
            (0.3 if node.subtype in ("person", "empire", "war") else 0.1)
        )

    return nodes, edges


# ============================================================================
# SUBGRAPH EXTRACTION
# ============================================================================

def extract_subgraph(
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
    seed_names: list[str],
    *,
    max_depth: int = 2,
) -> tuple[dict[str, GraphNode], list[GraphEdge]]:
    """Extract a subgraph around seed nodes up to max_depth hops."""
    included: set[str] = set(seed_names)

    for _depth in range(max_depth):
        new_names: set[str] = set()
        for edge in edges:
            if edge.subject in included and edge.object in nodes:
                new_names.add(edge.object)
            if edge.object in included and edge.subject in nodes:
                new_names.add(edge.subject)
        included.update(new_names)

    sub_nodes = {n: nodes[n] for n in included if n in nodes}
    sub_edges = [e for e in edges if e.subject in included and e.object in included]
    return sub_nodes, sub_edges


# ============================================================================
# RANKING
# ============================================================================

def rank_nodes(nodes: dict[str, GraphNode], *, top_n: int = 15) -> list[GraphNode]:
    """Rank nodes by importance and return top N."""
    return sorted(nodes.values(), key=lambda n: n.importance, reverse=True)[:top_n]


# ============================================================================
# CLUSTERING
# ============================================================================

CLUSTER_RULES: dict[str, dict[str, object]] = {
    "Filosofía": {"subtypes": {"person"}, "keywords": {"filosofía", "philosophy", "filósofo", "enseñó", "taught", "academia", "liceo"}},
    "Conquista y Expansión": {"subtypes": {"person", "battle", "war"}, "keywords": {"conquistó", "conquered", "batalla", "battle", "derrotó", "defeated", "ejército", "military"}},
    "Imperios": {"subtypes": {"empire", "organization"}, "keywords": {"imperio", "empire", "fundó", "founded", "gobernó", "ruled"}},
    "Geografía y Lugares": {"subtypes": {"country", "city", "place", "empire", "continent"}, "keywords": {}},
    "Eventos": {"subtypes": {"battle", "war", "revolution", "historical_event"}, "keywords": {"batalla", "guerra", "revolución"}},
}


def build_clusters(
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
    notes: list[tuple[str, dict[str, object], str]] | None = None,
) -> list[Cluster]:
    """Build semantic clusters from graph nodes."""
    clusters: list[Cluster] = []

    for cluster_name, rules in CLUSTER_RULES.items():
        subtypes = rules.get("subtypes", set())
        keywords = rules.get("keywords", set())
        members: list[str] = []

        for node in nodes.values():
            if node.subtype in subtypes:
                members.append(node.name)
                continue
            # Check keywords in edges
            for edge in edges:
                if edge.subject == node.name or edge.object == node.name:
                    pred = (edge.predicate or "").lower()
                    if any(kw in pred for kw in keywords):
                        members.append(node.name)
                        break

        members = sorted(set(members))
        if members:
            clusters.append(Cluster(
                name=cluster_name,
                nodes=members,
                description=f"{len(members)} entidades relacionadas con {cluster_name.lower()}",
            ))

    return [c for c in clusters if len(c.nodes) >= 1]


# ============================================================================
# ROUTE GENERATION
# ============================================================================

ROUTE_PREDICATES = {
    "influence": {"taught", "mentor_of", "studied_under", "influenced", "influenced_by"},
    "lineage": {"parent_of", "child_of", "succeeded", "preceded_by"},
    "conflict": {"defeated", "conquered", "opposed", "fought_in"},
    "creation": {"founded", "ruled", "led", "part_of"},
}


def _find_chain(
    start: str,
    adjacency: dict[str, list[str]],
    nodes: dict[str, GraphNode],
    *,
    max_length: int = 5,
    min_importance: float = 0.3,
) -> list[str]:
    """Find a chain of important connected nodes starting from start."""
    chain = [start]
    visited = {start}

    for _ in range(max_length - 1):
        current = chain[-1]
        neighbors = adjacency.get(current, [])
        best = None
        best_score = -1
        for neighbor in neighbors:
            if neighbor in visited:
                continue
            node = nodes.get(neighbor)
            if node and node.importance >= min_importance and node.importance > best_score:
                best = neighbor
                best_score = node.importance
        if best is None:
            break
        chain.append(best)
        visited.add(best)

    return chain


def generate_routes(
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
    *,
    max_routes: int = 5,
) -> list[Route]:
    """Generate meaningful exploration routes from the graph."""
    # Build adjacency
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.subject, []).append(edge.object)
        adjacency.setdefault(edge.object, []).append(edge.subject)

    # Start from highest importance nodes
    top_nodes = rank_nodes(nodes, top_n=8)
    routes: list[Route] = []
    used_starts: set[str] = set()

    for start_node in top_nodes:
        if start_node.name in used_starts:
            continue
        chain = _find_chain(start_node.name, adjacency, nodes, max_length=5)
        if len(chain) >= 3:
            # Generate narrative
            first = chain[0]
            last = chain[-1]
            narrative = f"De [[{first}]] a [[{last}]] — {len(chain)} pasos por el conocimiento conectado"
            routes.append(Route(
                title=f"{first} → {last}",
                path=chain,
                narrative=narrative,
            ))
            used_starts.add(start_node.name)

        if len(routes) >= max_routes:
            break

    return routes


# ============================================================================
# QUESTION GENERATION
# ============================================================================

QUESTION_TEMPLATES = [
    "¿Qué relación hay entre [[{a}]] y [[{b}]]?",
    "¿Por qué [[{a}]] fue importante para [[{b}]]?",
    "¿Cómo cambió [[{b}]] después de [[{a}]]?",
    "¿Qué diferencia a [[{a}]] de [[{b}]]?",
]


def generate_questions(
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
    *,
    max_questions: int = 7,
) -> list[str]:
    """Generate guiding questions from graph structure."""
    questions: list[str] = []
    top = rank_nodes(nodes, top_n=6)

    # Compare top nodes pairwise
    for i, node_a in enumerate(top):
        for node_b in top[i + 1:]:
            if len(questions) >= max_questions:
                break
            # Check if they're connected
            connected = any(
                (e.subject == node_a.name and e.object == node_b.name) or
                (e.subject == node_b.name and e.object == node_a.name)
                for e in edges
            )
            template_idx = 0 if connected else 3
            question = QUESTION_TEMPLATES[template_idx % len(QUESTION_TEMPLATES)].format(
                a=node_a.name, b=node_b.name,
            )
            questions.append(question)

    return questions[:max_questions]


# ============================================================================
# TIMELINE EXTRACTION
# ============================================================================

def extract_timeline(notes: list[tuple[str, dict[str, object], str]]) -> list[tuple[str, str]]:
    """Extract timeline entries from entity notes."""
    entries: list[tuple[str, str, float]] = []

    for _path, fm, body in notes:
        if fm.get("entity") is not True:
            continue
        name = fm.get("name", "")
        # Extract from body: lines starting with - **date** —
        for line in body.splitlines():
            match = re.match(r"^-\s+\*\*(.+?)\*\*\s*[—–-]\s*(.+)", line.strip())
            if match:
                date_str = match.group(1).strip()
                event = match.group(2).strip()
                # Try to extract a sortable year
                year_match = re.search(r"(\d{3,4})", date_str)
                sort_key = -int(year_match.group(1)) if year_match else 0
                entries.append((date_str, f"{event}", sort_key))

    # Sort by year (negative = BC, so sort ascending)
    entries.sort(key=lambda x: x[2])
    # Deduplicate similar entries
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for date, event, _ in entries:
        key = f"{date}|{event[:30]}"
        if key not in seen:
            seen.add(key)
            unique.append((date, event))
    return unique[:25]


# ============================================================================
# MOC RENDERING
# ============================================================================

AUTO_START = "<!-- AUTO:START -->"
AUTO_END = "<!-- AUTO:END -->"


def preserve_manual_sections(existing_content: str, new_content: str) -> str:
    """Merge auto-generated content while preserving manual edits outside AUTO markers."""
    if AUTO_START not in existing_content:
        return new_content

    # Extract manual sections (before first AUTO:START and after last AUTO:END)
    first_auto = existing_content.find(AUTO_START)
    last_auto_end = existing_content.rfind(AUTO_END)

    manual_before = existing_content[:first_auto].rstrip() if first_auto > 0 else ""
    manual_after = existing_content[last_auto_end + len(AUTO_END):].lstrip() if last_auto_end > 0 else ""

    # Wrap new content in AUTO markers
    auto_block = f"{AUTO_START}\n{new_content}\n{AUTO_END}"

    parts: list[str] = []
    if manual_before:
        parts.append(manual_before)
    parts.append(auto_block)
    if manual_after:
        parts.append(manual_after)

    return "\n\n".join(parts)


def render_moc_markdown(moc: GeneratedMOC, *, wrap_auto: bool = True) -> str:
    """Render a GeneratedMOC as markdown."""
    lines: list[str] = [
        "---",
        "type: map",
        "tags:",
        "  - moc",
        "  - auto-generated",
        "status: active",
        "---",
        "",
        f"# {moc.topic}",
        "",
        moc.description,
        "",
        "---",
        "",
    ]

    if wrap_auto:
        lines.append(AUTO_START)
        lines.append("")

    # Timeline
    if moc.timeline_entries:
        lines.append("## Línea Temporal")
        lines.append("")
        lines.append("```")
        for date, event in moc.timeline_entries:
            lines.append(f" {date:>12}  → {event}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Top nodes
    if moc.top_nodes:
        lines.append("## Nodos Centrales")
        lines.append("")
        for node in moc.top_nodes[:10]:
            kind_label = f"{node.object_kind}/{node.subtype}" if node.subtype else node.object_kind
            lines.append(f"- [[{node.name}]] — *{kind_label}* (importancia: {node.importance:.1f})")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Clusters
    if moc.clusters:
        lines.append("## Clusters")
        lines.append("")
        for cluster in moc.clusters:
            lines.append(f"### {cluster.name}")
            for name in cluster.nodes:
                lines.append(f"- [[{name}]]")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Key relations
    if moc.key_relations:
        lines.append("## Relaciones Clave")
        lines.append("")
        for edge in moc.key_relations[:15]:
            pred = edge.predicate or "related_to"
            lines.append(f"- [[{edge.subject}]] — {pred} → [[{edge.object}]]")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Routes
    if moc.routes:
        lines.append("## Rutas de Exploración")
        lines.append("")
        for route in moc.routes:
            path_str = " → ".join(f"[[{n}]]" for n in route.path)
            lines.append(f"### {route.title}")
            lines.append(f"{path_str}")
            lines.append(f"*{route.narrative}*")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Questions
    if moc.questions:
        lines.append("## Preguntas para Explorar")
        lines.append("")
        for q in moc.questions:
            lines.append(f"- {q}")
        lines.append("")

    if wrap_auto:
        lines.append(AUTO_END)
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_moc(
    topic: str,
    notes: list[tuple[str, dict[str, object], str]],
    *,
    seed_names: list[str] | None = None,
    max_depth: int = 2,
    description: str | None = None,
) -> GeneratedMOC:
    """Generate a MOC from vault notes for a given topic."""
    all_nodes, all_edges = build_graph_from_vault(notes)

    # If seed names provided, extract subgraph
    if seed_names:
        nodes, edges = extract_subgraph(all_nodes, all_edges, seed_names, max_depth=max_depth)
    else:
        nodes, edges = all_nodes, all_edges

    top_nodes = rank_nodes(nodes, top_n=15)
    clusters = build_clusters(nodes, edges, notes)
    key_relations = [e for e in edges if e.subject in nodes and e.object in nodes][:15]
    routes = generate_routes(nodes, edges, max_routes=5)
    questions = generate_questions(nodes, edges, max_questions=7)
    timeline = extract_timeline(notes)

    return GeneratedMOC(
        topic=topic,
        description=description or f"Mapa de navegación auto-generado para {topic}.",
        top_nodes=top_nodes,
        clusters=clusters,
        key_relations=key_relations,
        routes=routes,
        questions=questions,
        timeline_entries=timeline,
    )


__all__ = [
    "Cluster",
    "GeneratedMOC",
    "GraphEdge",
    "GraphNode",
    "Route",
    "build_graph_from_vault",
    "generate_moc",
    "preserve_manual_sections",
    "render_moc_markdown",
]
