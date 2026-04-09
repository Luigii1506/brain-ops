from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge import build_direct_edit_extraction


class BuildDirectEditExtractionTestCase(TestCase):
    def test_builds_richer_extraction_from_sections(self) -> None:
        frontmatter = {
            "type": "person",
            "related": ["Aristóteles", "Imperio Persa"],
        }
        body = """
## Identity

- Rey de Macedonia y conquistador helenístico.

## Key Facts

- Nació en 356 a.C.
- Fue alumno de Aristóteles.

## Timeline

- **356 a.C.** — Nace en Pella.
- **334 a.C.** — Cruza al Asia Menor.

## Impact

- Transformó el equilibrio político del Mediterráneo oriental.

## Strategic Insights

- Integró conquista militar con fundación de ciudades.

## Contradictions & Uncertainties

- Existen versiones conflictivas sobre algunos episodios de su juventud.
"""
        extraction = build_direct_edit_extraction(
            frontmatter,
            body,
            name="Alejandro Magno",
            source_url="https://es.wikipedia.org/wiki/Alejandro_Magno",
        )

        self.assertEqual(extraction["title"], "Alejandro Magno")
        self.assertEqual(extraction["source_type"], "direct_edit")
        self.assertEqual(extraction["source_url"], "https://es.wikipedia.org/wiki/Alejandro_Magno")
        self.assertIn("Rey de Macedonia", extraction["summary"])
        self.assertTrue(extraction["tldr"])
        self.assertIn("Nació en 356 a.C.", extraction["core_facts"])
        self.assertIn("Transformó el equilibrio político", extraction["key_insights"][0])
        self.assertEqual(extraction["timeline"][0]["date"], "356 a.C.")
        self.assertEqual(extraction["timeline"][0]["event"], "Nace en Pella.")
        self.assertEqual(extraction["entities"][0]["name"], "Alejandro Magno")
        self.assertEqual(extraction["relationships"][0]["object"], "Aristóteles")
        self.assertIn(
            "Integró conquista militar con fundación de ciudades.",
            extraction["strategic_patterns"],
        )
        self.assertIn(
            "Existen versiones conflictivas sobre algunos episodios de su juventud.",
            extraction["contradictions_or_uncertainties"],
        )

    def test_handles_missing_sections_and_string_related(self) -> None:
        extraction = build_direct_edit_extraction(
            {"type": "concept", "related": "Roma"},
            "Texto libre sin headings formales.",
            name="Imperium",
        )

        self.assertEqual(extraction["summary"], "Texto libre sin headings formales.")
        self.assertEqual(extraction["tldr"], "Texto libre sin headings formales.")
        self.assertEqual(extraction["timeline"], [])
        self.assertEqual(extraction["relationships"][0]["object"], "Roma")
        self.assertIsNone(extraction["personal_relevance"])
