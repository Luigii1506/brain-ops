"""API routes for knowledge entities."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from brain_ops.domains.knowledge.entities import ENTITY_TYPES
from brain_ops.storage.sqlite.entities import (
    read_compiled_entities,
    read_compiled_entity,
    read_entity_connections,
    traverse_entity_graph,
)

from .dependencies import resolve_knowledge_db_path

router = APIRouter()


@router.get("/")
def list_entities(entity_type: str | None = None):
    """List all compiled knowledge entities, optionally filtered by type."""
    db_path = resolve_knowledge_db_path()
    entities = read_compiled_entities(db_path)
    if entity_type:
        entities = [e for e in entities if e.entity_type == entity_type]
    return [e.to_dict() for e in entities]


@router.get("/types")
def list_entity_types():
    """List all supported entity types."""
    return {name: description for name, description in ENTITY_TYPES.items()}


@router.get("/search/{query}")
def search_entities(query: str, max_results: int = 20):
    """Search entities by name (substring match)."""
    db_path = resolve_knowledge_db_path()
    entities = read_compiled_entities(db_path)
    query_lower = query.lower()
    matches = [
        e.to_dict() for e in entities
        if query_lower in e.name.lower() or query_lower in e.entity_type.lower()
    ]
    return matches[:max_results]


@router.get("/{name}")
def get_entity(name: str):
    """Get a single entity by name."""
    db_path = resolve_knowledge_db_path()
    entity = read_compiled_entity(db_path, name)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{name}' not found.")
    return entity.to_dict()


@router.get("/{name}/relations")
def get_entity_relations(name: str):
    """Get all entities connected to a given entity."""
    db_path = resolve_knowledge_db_path()
    entity = read_compiled_entity(db_path, name)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{name}' not found.")
    connections = read_entity_connections(db_path, name)
    return {
        "entity": name,
        "connections": connections,
        "total": len(connections),
    }


@router.get("/{name}/graph")
def get_entity_graph(name: str, depth: int = 2):
    """Traverse the entity graph from a starting entity up to N hops."""
    db_path = resolve_knowledge_db_path()
    entity = read_compiled_entity(db_path, name)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{name}' not found.")
    graph = traverse_entity_graph(db_path, name, max_depth=min(depth, 4))
    return {
        "entity": name,
        "depth": depth,
        "graph": graph,
    }
