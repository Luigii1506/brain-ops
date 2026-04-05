from __future__ import annotations

import re
from pathlib import Path
from unittest import TestCase


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
TESTS_ROOT = REPO_ROOT / "tests"


class LegacySurfaceBoundariesTestCase(TestCase):
    def test_src_does_not_import_removed_conversation_compat_wrappers(self) -> None:
        removed_modules = {
            "brain_ops.services.handle_input_service",
            "brain_ops.services.intent_parser_service",
            "brain_ops.services.router_service",
            "brain_ops.services.intent_formatter_service",
            "brain_ops.services.follow_up_service",
            "brain_ops.services.intent_execution_service",
        }

        offenders = self._find_import_offenders(removed_modules)
        self.assertEqual(offenders, [])

    def test_src_does_not_import_reporting_compatibility_facade(self) -> None:
        offenders = self._find_import_offenders({"brain_ops.reporting"})
        self.assertEqual(offenders, [])

    def test_tests_do_not_import_removed_conversation_compat_wrappers(self) -> None:
        removed_modules = {
            "brain_ops.services.handle_input_service",
            "brain_ops.services.intent_parser_service",
            "brain_ops.services.router_service",
            "brain_ops.services.intent_formatter_service",
            "brain_ops.services.follow_up_service",
            "brain_ops.services.intent_execution_service",
        }
        offenders = self._find_import_offenders(
            removed_modules,
            root=TESTS_ROOT,
        )
        self.assertEqual(offenders, [])

    def test_tests_only_use_reporting_facade_in_explicit_compat_suite(self) -> None:
        offenders = self._find_import_offenders(
            {"brain_ops.reporting", "brain_ops"},
            root=TESTS_ROOT,
            allowed_paths={"tests/test_reporting_facade_and_cli_app.py"},
            custom_matcher=self._contains_reporting_import,
        )
        self.assertEqual(offenders, [])

    def _find_import_offenders(
        self,
        module_names: set[str],
        *,
        root: Path = SRC_ROOT,
        allowed_paths: set[str] | None = None,
        custom_matcher=None,
    ) -> list[str]:
        offenders: list[str] = []
        allowed_paths = allowed_paths or set()
        for path in root.rglob("*.py"):
            relative_path = str(path.relative_to(REPO_ROOT))
            if relative_path in allowed_paths:
                continue
            text = path.read_text(encoding="utf-8")
            for module_name in module_names:
                matcher = custom_matcher or self._contains_import
                if matcher(text, module_name):
                    offenders.append(relative_path)
                    break
        return sorted(offenders)

    @staticmethod
    def _contains_import(text: str, module_name: str) -> bool:
        escaped = re.escape(module_name)
        patterns = (
            rf"^\s*from\s+{escaped}\s+import\s+",
            rf"^\s*import\s+{escaped}(?:\s|$)",
        )
        return any(re.search(pattern, text, flags=re.MULTILINE) for pattern in patterns)

    @staticmethod
    def _contains_reporting_import(text: str, module_name: str) -> bool:
        if module_name == "brain_ops.reporting":
            patterns = (
                r"^\s*from\s+brain_ops\.reporting\s+import\s+",
                r"^\s*import\s+brain_ops\.reporting(?:\s|$)",
            )
            return any(re.search(pattern, text, flags=re.MULTILINE) for pattern in patterns)

        patterns = (
            r"^\s*from\s+brain_ops\s+import\s+reporting(?:\s|$)",
            r"^\s*import\s+brain_ops\.reporting(?:\s|$)",
        )
        return any(re.search(pattern, text, flags=re.MULTILINE) for pattern in patterns)


if __name__ == "__main__":
    import unittest

    unittest.main()
