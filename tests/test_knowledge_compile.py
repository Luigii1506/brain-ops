from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.compile import (
    CompileResult,
    CompiledEntity,
    CompiledRelation,
    compile_entity_from_frontmatter,
    compile_relations_from_frontmatter,
    compile_vault_entities,
)
from brain_ops.storage.sqlite.entities import (
    initialize_entity_tables,
    read_compiled_entities,
    read_compiled_entity,
    read_entity_connections,
    write_compiled_entities,
)


class CompileEntityFromFrontmatterTestCase(TestCase):
    def test_compiles_person_entity(self) -> None:
        fm = {"entity": True, "type": "person", "name": "Napoleón", "born": "1769", "nationality": "Francia"}
        entity = compile_entity_from_frontmatter(fm, "02 - Knowledge/Napoleón.md")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, "Napoleón")
        self.assertEqual(entity.entity_type, "person")
        self.assertEqual(entity.relative_path, "02 - Knowledge/Napoleón.md")
        self.assertEqual(entity.metadata["born"], "1769")
        self.assertNotIn("type", entity.metadata)
        self.assertNotIn("entity", entity.metadata)

    def test_returns_none_for_non_entity(self) -> None:
        fm = {"type": "source", "name": "Article"}
        self.assertIsNone(compile_entity_from_frontmatter(fm, "test.md"))

    def test_returns_none_for_missing_name(self) -> None:
        fm = {"entity": True, "type": "person"}
        self.assertIsNone(compile_entity_from_frontmatter(fm, "test.md"))

    def test_excludes_none_values_from_metadata(self) -> None:
        fm = {"entity": True, "type": "concept", "name": "Gravity", "field": None, "originated": "17th century"}
        entity = compile_entity_from_frontmatter(fm, "test.md")
        self.assertNotIn("field", entity.metadata)
        self.assertEqual(entity.metadata["originated"], "17th century")


class CompileRelationsTestCase(TestCase):
    def test_compiles_relations_from_related_field(self) -> None:
        fm = {"entity": True, "type": "person", "name": "Alejandro", "related": ["Aristóteles", "Darío"]}
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        self.assertEqual(rels[0].source_entity, "Alejandro")
        self.assertEqual(rels[0].target_entity, "Aristóteles")
        self.assertEqual(rels[0].source_type, "person")

    def test_returns_empty_for_non_entity(self) -> None:
        fm = {"type": "source", "related": ["something"]}
        self.assertEqual(compile_relations_from_frontmatter(fm), [])


class CompileVaultEntitiesTestCase(TestCase):
    def test_compiles_multiple_entities_and_relations(self) -> None:
        notes = [
            ("a.md", {"entity": True, "type": "person", "name": "A", "related": ["B"]}),
            ("b.md", {"entity": True, "type": "place", "name": "B", "related": ["A"]}),
            ("c.md", {"type": "source", "name": "Article"}),
        ]
        result = compile_vault_entities(notes)
        self.assertEqual(len(result.entities), 2)
        self.assertEqual(len(result.relations), 2)
        self.assertEqual(result.entities[0].name, "A")
        self.assertEqual(result.entities[1].name, "B")


class SqliteEntityStorageTestCase(TestCase):
    def test_write_and_read_entities_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge.db"
            result = CompileResult(
                entities=[
                    CompiledEntity(name="Napoleón", entity_type="person", relative_path="n.md", metadata={"born": "1769"}),
                    CompiledEntity(name="Francia", entity_type="place", relative_path="f.md", metadata={"capital": "París"}),
                ],
                relations=[
                    CompiledRelation(source_entity="Napoleón", target_entity="Francia", source_type="person"),
                ],
            )
            total = write_compiled_entities(db_path, result)
            self.assertEqual(total, 2)

            entities = read_compiled_entities(db_path)
            self.assertEqual(len(entities), 2)
            self.assertEqual(entities[1].name, "Napoleón")
            self.assertEqual(entities[1].metadata["born"], "1769")

    def test_read_single_entity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge.db"
            result = CompileResult(
                entities=[
                    CompiledEntity(name="Grecia", entity_type="place", relative_path="g.md", metadata={"capital": "Atenas"}),
                ],
                relations=[],
            )
            write_compiled_entities(db_path, result)

            entity = read_compiled_entity(db_path, "Grecia")
            self.assertIsNotNone(entity)
            self.assertEqual(entity.entity_type, "place")
            self.assertEqual(entity.metadata["capital"], "Atenas")

            missing = read_compiled_entity(db_path, "Nonexistent")
            self.assertIsNone(missing)

    def test_read_entity_connections(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge.db"
            result = CompileResult(
                entities=[
                    CompiledEntity(name="A", entity_type="person", relative_path="a.md", metadata={}),
                    CompiledEntity(name="B", entity_type="place", relative_path="b.md", metadata={}),
                    CompiledEntity(name="C", entity_type="event", relative_path="c.md", metadata={}),
                ],
                relations=[
                    CompiledRelation(source_entity="A", target_entity="B", source_type="person"),
                    CompiledRelation(source_entity="A", target_entity="C", source_type="person"),
                    CompiledRelation(source_entity="B", target_entity="C", source_type="place"),
                ],
            )
            write_compiled_entities(db_path, result)

            connections = read_entity_connections(db_path, "A")
            self.assertEqual(connections, ["B", "C"])

            connections_b = read_entity_connections(db_path, "B")
            self.assertIn("A", connections_b)
            self.assertIn("C", connections_b)

    def test_write_replaces_previous_data(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge.db"
            result1 = CompileResult(
                entities=[CompiledEntity(name="Old", entity_type="person", relative_path="o.md", metadata={})],
                relations=[],
            )
            write_compiled_entities(db_path, result1)

            result2 = CompileResult(
                entities=[CompiledEntity(name="New", entity_type="place", relative_path="n.md", metadata={})],
                relations=[],
            )
            write_compiled_entities(db_path, result2)

            entities = read_compiled_entities(db_path)
            self.assertEqual(len(entities), 1)
            self.assertEqual(entities[0].name, "New")

    def test_read_from_nonexistent_db_returns_empty(self) -> None:
        self.assertEqual(read_compiled_entities(Path("/tmp/nonexistent_12345.db")), [])
        self.assertIsNone(read_compiled_entity(Path("/tmp/nonexistent_12345.db"), "X"))
        self.assertEqual(read_entity_connections(Path("/tmp/nonexistent_12345.db"), "X"), [])


if __name__ == "__main__":
    import unittest

    unittest.main()
