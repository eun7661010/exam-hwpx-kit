from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from pydantic import ValidationError

from exam_hwpx_kit.models import ExamPaper, PassageBlock, QuestionBlock


def test_checked_in_schema_accepts_public_example(repo_root: Path, example_payload: dict) -> None:
    schema_path = repo_root / "src" / "exam_hwpx_kit" / "schemas" / "exam-paper.v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(example_payload)


def test_model_rejects_unknown_fields(example_payload: dict) -> None:
    example_payload["private_note"] = "must fail"
    try:
        ExamPaper.model_validate(example_payload)
    except ValidationError as exc:
        assert "private_note" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown field was accepted")


def test_question_union_is_discriminated(example_exam: ExamPaper) -> None:
    assert isinstance(example_exam.blocks[0], PassageBlock)
    assert isinstance(example_exam.blocks[1], QuestionBlock)


def test_question_choice_bounds(example_payload: dict) -> None:
    example_payload["blocks"][1]["choices"] = ["one"]
    try:
        ExamPaper.model_validate(example_payload)
    except ValidationError as exc:
        assert "at least 2" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("short choice list was accepted")


def test_only_version_one_is_accepted(example_payload: dict) -> None:
    example_payload["schema_version"] = "exam-hwpx-kit/v2"
    try:
        ExamPaper.model_validate(example_payload)
    except ValidationError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unknown schema version was accepted")
