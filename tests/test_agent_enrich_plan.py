from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge import build_direct_enrich_plan, save_direct_enrich_plan


class DirectEnrichPlanTestCase(TestCase):
    def test_build_direct_enrich_plan_creates_passes_ranked_chunks_and_steps(self) -> None:
        raw_text = """
Biography
[
editar
]
Albert Einstein was born in Ulm and later studied at ETH Zurich. His education and early life mattered.

Scientific career
[
editar
]
In 1905 he published papers on the photoelectric effect, Brownian motion, and special relativity.

General relativity
[
editar
]
By 1915 Einstein completed the field equations of general relativity and changed cosmology.

Political views
[
editar
]
He spoke against fascism, supported civil rights, and commented on Zionism and nuclear weapons.
"""

        plan = build_direct_enrich_plan(
            entity_name="Albert Einstein",
            source_url="https://en.wikipedia.org/wiki/Albert_Einstein",
            raw_text=raw_text,
            raw_file=Path("/tmp/albert-einstein.txt"),
            subtype="person",
        )

        self.assertEqual(plan.entity_name, "Albert Einstein")
        self.assertEqual(plan.mode, "deep")
        self.assertTrue(plan.pass_plans)
        self.assertTrue(plan.ranked_chunks)
        self.assertTrue(all(enrich_pass.context.strip() for enrich_pass in plan.pass_plans))
        self.assertIn("run brain post-process", plan.workflow_steps[3].lower())

    def test_save_direct_enrich_plan_writes_json_file(self) -> None:
        plan = build_direct_enrich_plan(
            entity_name="Albert Einstein",
            source_url="https://en.wikipedia.org/wiki/Albert_Einstein",
            raw_text="Short but useful text about Einstein and relativity.",
            raw_file=Path("/tmp/albert-einstein.txt"),
            subtype="person",
        )

        with TemporaryDirectory() as tmpdir:
            path = save_direct_enrich_plan(Path(tmpdir), plan)
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["entity_name"], "Albert Einstein")
            self.assertEqual(data["raw_file"], "/tmp/albert-einstein.txt")
            self.assertIn("passes", data)
