from __future__ import annotations

from pathlib import Path

import pytest

from exam_hwpx_kit.models import ExamPaper
from exam_hwpx_kit.validation import load_and_validate, validate_exam


def codes(exam: ExamPaper, root: Path) -> set[str]:
    return {issue.code for issue in validate_exam(exam, root=root).issues}


def test_example_passes(example_exam: ExamPaper, example_path: Path) -> None:
    report = validate_exam(example_exam, root=example_path.parent)
    assert report.ok
    assert report.errors == 0
    assert report.warnings == 0


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda p: p["blocks"][2].update(id="q1"), "duplicate-block-id"),
        (lambda p: p["blocks"][2].update(number=1), "duplicate-question-number"),
        (lambda p: p["blocks"][0]["question_ids"].append("q1"), "duplicate-passage-reference"),
        (lambda p: p["blocks"][0]["question_ids"].append("q9"), "missing-passage-question"),
        (lambda p: p["blocks"][1]["choices"].__setitem__(0, "① marked"), "embedded-choice-marker"),
        (lambda p: p["blocks"][1]["image_ids"].append("missing"), "missing-image-reference"),
        (lambda p: p["blocks"][1].update(stem="bad\x00text"), "unsafe-control-character"),
        (lambda p: p["assets"][0].update(path="missing.png"), "missing-asset-file"),
        (lambda p: p["assets"][0].update(path="asset.svg"), "unsupported-image-format"),
        (
            lambda p: p["assets"].append({"id": "sensor-chart", "path": "x.png", "alt": "x"}),
            "duplicate-asset-id",
        ),
    ],
)
def test_semantic_failures(
    example_payload: dict, example_path: Path, mutation, expected: str
) -> None:
    mutation(example_payload)
    exam = ExamPaper.model_validate(example_payload)
    assert expected in codes(exam, example_path.parent)


def test_absolute_windows_path_is_rejected(example_payload: dict, example_path: Path) -> None:
    example_payload["assets"][0]["path"] = "C:\\Private\\chart.png"
    exam = ExamPaper.model_validate(example_payload)
    assert "absolute-asset-path" in codes(exam, example_path.parent)


def test_path_traversal_is_rejected(example_payload: dict, example_path: Path) -> None:
    example_payload["assets"][0]["path"] = "../outside.png"
    exam = ExamPaper.model_validate(example_payload)
    assert "asset-path-escape" in codes(exam, example_path.parent)


def test_orphan_asset_is_warning(example_payload: dict, example_path: Path) -> None:
    example_payload["blocks"][2]["image_ids"] = []
    exam = ExamPaper.model_validate(example_payload)
    report = validate_exam(exam, root=example_path.parent)
    assert report.ok
    assert "orphan-asset" in {issue.code for issue in report.issues}


def test_large_keep_together_question_fails(example_payload: dict, example_path: Path) -> None:
    example_payload["blocks"][1]["stem"] = "긴 문장 " * 500
    example_payload["layout"]["max_lines_per_column"] = 20
    exam = ExamPaper.model_validate(example_payload)
    assert "keep-together-overflow-risk" in codes(exam, example_path.parent)


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    exam, report = load_and_validate(path)
    assert exam is None
    assert report.ok is False
    assert report.issues[0].code == "invalid-json"


def test_load_schema_failure(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":"wrong"}', encoding="utf-8")
    exam, report = load_and_validate(path)
    assert exam is None
    assert any(issue.code == "schema" for issue in report.issues)
