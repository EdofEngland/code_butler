from __future__ import annotations

from pathlib import Path

import pytest

from ai_clean.config import SpecBackendConfig
from ai_clean.models import ButlerSpec, CleanupPlan
from ai_clean.spec_backends import ButlerSpecBackend


def make_backend(
    *, specs_dir: Path | None = None, **kwargs: object
) -> ButlerSpecBackend:
    config = SpecBackendConfig(
        type="butler",
        default_batch_group="default",
        specs_dir=specs_dir or Path(".ai-clean/specs"),
    )
    return ButlerSpecBackend(config, **kwargs)


def _sample_plan(**overrides: object) -> CleanupPlan:
    base_payload: dict[str, object] = {
        "id": " plan-123 ",
        "finding_id": "finding-456",
        "title": "  Tighten foo.py ",
        "intent": "  Tighten foo.py ",
        "steps": [
            "  Add guard around condition ",
            "Refactor helper  ",
        ],
        "constraints": ["  Touch only src/foo.py  "],
        "tests_to_run": ["  pytest tests/test_foo.py  "],
        "metadata": {
            "target_file": "  src/foo.py  ",
            "notes": "Existing metadata should survive",
        },
    }
    payload = {**base_payload, **overrides}
    return CleanupPlan(**payload)  # type: ignore[arg-type]


def test_plan_to_spec_happy_path():
    backend = make_backend()
    plan = _sample_plan()
    original = plan.model_copy(deep=True)

    spec = backend.plan_to_spec(plan)

    assert spec.id == "plan-123-spec"
    assert spec.plan_id == "plan-123"
    assert spec.target_file == "src/foo.py"
    assert spec.intent == "Tighten foo.py"
    assert spec.model == "codex"
    assert spec.batch_group == "default"
    assert len(spec.actions) == 2
    assert spec.actions[0]["index"] == 1
    assert spec.actions[0]["summary"] == "Add guard around condition"
    assert spec.actions[1]["index"] == 2
    assert spec.actions[1]["summary"] == "Refactor helper"
    assert spec.metadata["plan_title"] == "Tighten foo.py"
    assert spec.metadata["constraints"] == ["Touch only src/foo.py"]
    assert spec.metadata["tests_to_run"] == ["pytest tests/test_foo.py"]
    assert spec.metadata["target_file"] == "src/foo.py"
    assert spec.metadata["notes"] == "Existing metadata should survive"
    assert spec.metadata is not plan.metadata
    assert plan.model_dump(mode="json") == original.model_dump(mode="json")


def test_plan_to_spec_requires_steps():
    backend = make_backend()
    plan = _sample_plan(steps=["  ", ""])

    with pytest.raises(ValueError, match="CleanupPlan must include at least one step"):
        backend.plan_to_spec(plan)


def test_plan_to_spec_requires_target_file():
    backend = make_backend()
    plan = _sample_plan(metadata={})

    with pytest.raises(
        ValueError, match="ButlerSpec plans must declare exactly one target_file"
    ):
        backend.plan_to_spec(plan)


def test_plan_to_spec_rejects_multiple_targets():
    backend = make_backend()
    plan = _sample_plan(
        metadata={
            "target_file": "src/foo.py",
            "target_file_candidates": ["src/foo.py", "src/bar.py"],
        }
    )

    with pytest.raises(
        ValueError, match="ButlerSpec plans must not declare multiple target files"
    ):
        backend.plan_to_spec(plan)


def test_plan_to_spec_rejects_oversized_metadata():
    backend = make_backend()
    plan = _sample_plan(
        metadata={
            "target_file": "src/foo.py",
            "notes": "x" * (33 * 1024),
        }
    )

    with pytest.raises(ValueError, match="ButlerSpec metadata exceeds the 32 KB limit"):
        backend.plan_to_spec(plan)


def test_plan_to_spec_validates_intent_path_alignment():
    backend = make_backend()
    plan = _sample_plan(intent="Adjust documentation only")

    with pytest.raises(
        ValueError,
        match="CleanupPlan intent must describe work in target_file 'src/foo.py'",
    ):
        backend.plan_to_spec(plan)


def test_plan_to_spec_returns_new_metadata_dict():
    backend = make_backend()
    plan = _sample_plan()

    spec = backend.plan_to_spec(plan)
    spec.metadata["constraints"].append("Injected constraint")
    spec.metadata["target_file"] = "elsewhere"

    assert plan.metadata["target_file"].strip() == "src/foo.py"
    assert "Injected constraint" not in plan.metadata.get("constraints", [])


def test_plan_to_spec_is_deterministic():
    backend = make_backend()
    plan = _sample_plan()

    first = backend.plan_to_spec(plan)
    second = backend.plan_to_spec(plan)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_plan_fixture_canonicalization():
    backend = make_backend()
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "plans" / "sample_plan.json"
    )
    plan = CleanupPlan.model_validate_json(fixture_path.read_text())

    spec = backend.plan_to_spec(plan)

    assert spec.plan_id == "sample-plan"
    assert spec.metadata["plan_title"] == "Harden foo.py tests"
    assert spec.actions[0]["summary"] == "Add regression test for foo.py"
    assert spec.actions[1]["summary"] == "Refactor helper"
    assert spec.metadata["constraints"] == [
        "Touch only src/foo.py",
        "Keep patch under 40 lines",
    ]
    assert spec.metadata["tests_to_run"] == ["pytest tests/test_foo.py"]
    assert spec.metadata["target_file"] == "src/foo.py"


def test_write_spec_round_trip(tmp_path):
    backend = make_backend(specs_dir=tmp_path / "specs")
    spec = backend.plan_to_spec(_sample_plan())

    spec_path = backend.write_spec(spec)

    assert spec_path.exists()
    assert spec_path.name.endswith(".butler.yaml")
    reloaded = ButlerSpec.from_yaml(spec_path.read_text(encoding="utf-8"))
    assert reloaded == spec


def test_write_spec_creates_parent_directories(tmp_path):
    backend = make_backend(specs_dir=tmp_path / "specs")
    spec = backend.plan_to_spec(_sample_plan())
    target_dir = tmp_path / "nested" / "output"

    spec_path = backend.write_spec(spec, target_dir)

    assert spec_path.parent == target_dir
    assert spec_path.exists()


def test_write_spec_guardrails(tmp_path):
    backend = make_backend(specs_dir=tmp_path / "specs")
    spec = backend.plan_to_spec(_sample_plan())

    conflicting = spec.model_copy(deep=True)
    conflicting.metadata["target_file_candidates"] = ["a.py", "b.py"]
    with pytest.raises(
        ValueError, match="ButlerSpec plans must not declare multiple target files"
    ):
        backend.write_spec(conflicting, tmp_path)

    too_many = spec.model_copy(deep=True)
    too_many.actions = [
        {
            "type": "plan_step",
            "index": idx + 1,
            "summary": f"step {idx}",
            "payload": None,
        }
        for idx in range(26)
    ]
    with pytest.raises(ValueError, match="ButlerSpec specs must not exceed 25 actions"):
        backend.write_spec(too_many, tmp_path)

    oversized = spec.model_copy(deep=True)
    oversized.metadata["notes"] = "x" * (33 * 1024)
    with pytest.raises(ValueError, match="ButlerSpec metadata exceeds the 32 KB limit"):
        backend.write_spec(oversized, tmp_path)

    assert not list(tmp_path.rglob("*.butler.yaml"))


def test_write_spec_deterministic_overwrite(tmp_path, caplog):
    backend = make_backend(specs_dir=tmp_path / "specs")
    spec = backend.plan_to_spec(_sample_plan())

    spec_path = backend.write_spec(spec)
    original = spec_path.read_text(encoding="utf-8")

    caplog.set_level("WARNING", logger="ai_clean.spec_backends.butler")
    caplog.clear()
    backend.write_spec(spec)
    assert spec_path.read_text(encoding="utf-8") == original
    assert not caplog.records

    mutated = spec.model_copy(deep=True)
    mutated.metadata["notes"] = "updated note"
    backend.write_spec(mutated)
    assert "updated note" in spec_path.read_text(encoding="utf-8")
    assert caplog.records


def test_write_spec_permission_error_bubbles(tmp_path, monkeypatch):
    backend = make_backend(specs_dir=tmp_path / "specs")
    spec = backend.plan_to_spec(_sample_plan())
    expected_path = tmp_path / f"{spec.id}.butler.yaml"

    original_write = Path.write_text

    def fake_write(
        self, data, encoding="utf-8", errors=None
    ):  # pragma: no cover - shim
        if self == expected_path:
            raise PermissionError("read-only directory")
        return original_write(self, data, encoding=encoding, errors=errors)  # type: ignore[call-arg]

    monkeypatch.setattr(Path, "write_text", fake_write)

    with pytest.raises(PermissionError, match="read-only directory"):
        backend.write_spec(spec, tmp_path)

    assert not expected_path.exists()
