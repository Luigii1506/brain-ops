from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless

from brain_ops.domains.knowledge.compile import CompileResult, CompiledEntity, CompiledRelation
from brain_ops.domains.projects.registry import save_project_registry, build_project
from brain_ops.domains.monitoring.sources import save_source_registry, build_monitor_source
from brain_ops.storage.sqlite.entities import write_compiled_entities

try:
    from fastapi.testclient import TestClient
    from brain_ops.interfaces.api.app import create_api_app

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@skipUnless(HAS_FASTAPI, "FastAPI not installed")
class EntityRoutesTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "knowledge.db"
        result = CompileResult(
            entities=[
                CompiledEntity(name="Napoleón", entity_type="person", relative_path="n.md", metadata={"born": "1769"}),
                CompiledEntity(name="Francia", entity_type="place", relative_path="f.md", metadata={"capital": "París"}),
            ],
            relations=[
                CompiledRelation(source_entity="Napoleón", target_entity="Francia", source_type="person"),
            ],
        )
        write_compiled_entities(self.db_path, result)

        import os
        os.environ["BRAIN_OPS_KNOWLEDGE_DB"] = str(self.db_path)
        self.app = create_api_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        import os
        os.environ.pop("BRAIN_OPS_KNOWLEDGE_DB", None)
        self.temp_dir.cleanup()

    def test_list_entities(self) -> None:
        response = self.client.get("/entities/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_list_entities_filtered_by_type(self) -> None:
        response = self.client.get("/entities/?entity_type=person")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Napoleón")

    def test_get_entity(self) -> None:
        response = self.client.get("/entities/Napoleón")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Napoleón")
        self.assertEqual(data["metadata"]["born"], "1769")

    def test_get_entity_not_found(self) -> None:
        response = self.client.get("/entities/Nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_get_entity_relations(self) -> None:
        response = self.client.get("/entities/Napoleón/relations")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["entity"], "Napoleón")
        self.assertIn("Francia", data["connections"])

    def test_list_entity_types(self) -> None:
        response = self.client.get("/entities/types")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("person", data)
        self.assertIn("event", data)


@skipUnless(HAS_FASTAPI, "FastAPI not installed")
class ProjectRoutesTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.registry_path = Path(self.temp_dir.name) / "projects.json"
        project = build_project("brain-ops", path="/home/user/brain-ops", stack=["python"])
        save_project_registry(self.registry_path, {"brain-ops": project})

        import os
        os.environ["BRAIN_OPS_PROJECT_REGISTRY"] = str(self.registry_path)
        self.app = create_api_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        import os
        os.environ.pop("BRAIN_OPS_PROJECT_REGISTRY", None)
        self.temp_dir.cleanup()

    def test_list_projects(self) -> None:
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "brain-ops")

    def test_get_project(self) -> None:
        response = self.client.get("/projects/brain-ops")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "brain-ops")

    def test_get_project_not_found(self) -> None:
        response = self.client.get("/projects/nonexistent")
        self.assertEqual(response.status_code, 404)


@skipUnless(HAS_FASTAPI, "FastAPI not installed")
class SourceRoutesTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.registry_path = Path(self.temp_dir.name) / "sources.json"
        source = build_monitor_source("blog", url="https://blog.example.com")
        save_source_registry(self.registry_path, {"blog": source})

        import os
        os.environ["BRAIN_OPS_SOURCE_REGISTRY"] = str(self.registry_path)
        self.app = create_api_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        import os
        os.environ.pop("BRAIN_OPS_SOURCE_REGISTRY", None)
        self.temp_dir.cleanup()

    def test_list_sources(self) -> None:
        response = self.client.get("/sources/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "blog")

    def test_get_source_not_found(self) -> None:
        response = self.client.get("/sources/nonexistent")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    import unittest

    unittest.main()
