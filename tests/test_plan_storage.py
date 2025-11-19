from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_clean.models import CleanupPlan
from ai_clean.storage import load_plan, save_plan


def _make_plan(plan_id: str = "plan-123") -> CleanupPlan:
    return CleanupPlan(
        id=plan_id,
        finding_id="finding-1",
        title="Sample",
        intent="Do something",
        steps=["step 1"],
        constraints=["constraint"],
        tests_to_run=["pytest"],
        metadata={"foo": "bar"},
    )


class PlanStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_save_and_load_round_trip(self) -> None:
        plan = _make_plan()
        path = save_plan(plan, plans_dir=self.dir)
        self.assertTrue(path.exists())

        restored = load_plan(plan.id, plans_dir=self.dir)
        self.assertEqual(plan.to_dict(), restored.to_dict())

    def test_slugifies_plan_id(self) -> None:
        plan = _make_plan("src/foo.py:split-task")
        path = save_plan(plan, plans_dir=self.dir)
        self.assertTrue(path.name.endswith(".json"))
        self.assertEqual(path.name, "src-foo.py-split-task.json")

    def test_load_missing_plan_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_plan("missing-plan", plans_dir=self.dir)

    def test_load_invalid_plan_raises_value_error(self) -> None:
        path = self.dir / "plan-invalid.json"
        path.write_text(json.dumps({"id": "plan-invalid"}), encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            load_plan("plan-invalid", plans_dir=self.dir)
        self.assertIn("plan-invalid", str(ctx.exception))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
