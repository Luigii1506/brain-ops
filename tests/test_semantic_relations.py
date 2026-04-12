from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from brain_ops.domains.knowledge.semantic_relations import (
    add_semantic_related_links,
    build_reciprocal_semantic_suggestion,
    suggest_semantic_relations,
)


class SemanticRelationsTestCase(TestCase):
    def test_suggests_existing_semantic_relations_and_missing_entities(self) -> None:
        current = """---
name: Jasón y los Argonautas
entity: true
related:
- Medea
- Afrodita
---

## Identity

Jasón y los Argonautas narra la expedición del Argo hacia Cólquide para obtener el Vellocino de Oro.

## Narrative

Medea, hechicera de Cólquide, ayuda a Jasón porque está enamorada por intervención divina.
El mito funciona como ciclo anterior a Troya y viaje de regreso contaminado.

## Related notes

- [[Medea]]
- [[Afrodita]]
"""
        medea = """---
name: Medea
entity: true
related:
- Helios
- Hécate
---

## Relationships

- [[Helios]] — descendant_of — su linaje solar legitima su escape y poder.
- [[Hécate]] — associated_with — diosa vinculada a su magia.
"""
        notes = {
            "Jasón y los Argonautas": (Path("Jasón y los Argonautas.md"), {}, current),
            "Medea": (Path("Medea.md"), {}, medea),
            "Helios": (Path("Helios.md"), {}, "---\nname: Helios\nentity: true\n---\n"),
            "Hécate": (Path("Hécate.md"), {}, "---\nname: Hécate\nentity: true\n---\n"),
            "Eros": (Path("Eros.md"), {}, "---\nname: Eros\nentity: true\n---\n"),
            "Guerra de Troya": (Path("Guerra de Troya.md"), {}, "---\nname: Guerra de Troya\nentity: true\n---\n"),
        }

        suggestions = suggest_semantic_relations("Jasón y los Argonautas", current, notes)
        by_name = {s.name: s for s in suggestions}

        self.assertIn("Helios", by_name)
        self.assertIn("Hécate", by_name)
        self.assertIn("Eros", by_name)
        self.assertIn("Guerra de Troya", by_name)
        self.assertIn("Vellocino de Oro", by_name)
        self.assertFalse(by_name["Vellocino de Oro"].exists)

    def test_add_semantic_related_links_updates_frontmatter_and_related_notes(self) -> None:
        text = """---
name: Example
entity: true
related:
- Medea
---

## Identity

Medea usa magia.

## Related notes

- [[Medea]]
"""
        notes = {
            "Example": (Path("Example.md"), {}, text),
            "Medea": (Path("Medea.md"), {}, "---\nname: Medea\nentity: true\n---\n"),
            "Hécate": (Path("Hécate.md"), {}, "---\nname: Hécate\nentity: true\n---\n"),
        }
        suggestions = suggest_semantic_relations("Example", text, notes)
        updated, applied = add_semantic_related_links(text, suggestions, min_confidence=0.7)

        self.assertEqual([s.name for s in applied], ["Medea", "Hécate"])
        self.assertIn("H\\xE9cate", updated)
        self.assertIn("[[Medea]] — related_to", updated)
        self.assertIn("[[Hécate]] — related_to", updated)
        self.assertIn("- [[Hécate]]", updated)

    def test_build_reciprocal_semantic_suggestion_preserves_context(self) -> None:
        original = next(
            s for s in suggest_semantic_relations(
                "Example",
                """---
name: Example
entity: true
related:
- Medea
---

## Identity

Medea está enamorada y usa magia.
""",
                {
                    "Example": (Path("Example.md"), {}, ""),
                    "Eros": (Path("Eros.md"), {}, "---\nname: Eros\nentity: true\n---\n"),
                },
            )
            if s.name == "Eros"
        )

        reciprocal = build_reciprocal_semantic_suggestion("Example", original)

        self.assertEqual(reciprocal.name, "Example")
        self.assertEqual(reciprocal.predicate, original.predicate)
        self.assertIn("[[Example]]", reciprocal.reason)
        self.assertTrue(reciprocal.exists)
